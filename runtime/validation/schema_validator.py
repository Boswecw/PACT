from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "99-contracts" / "schemas"


@dataclass
class PacketValidationError(Exception):
    message: str
    public_reason_code: str = "validation_failed"
    failure_state: str = "validation_failure"

    def __str__(self) -> str:
        return self.message


@lru_cache(maxsize=1)
def _build_registry() -> Registry:
    registry = Registry()
    for path in SCHEMA_DIR.glob("*.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(path.resolve().as_uri(), resource)
        registry = registry.with_resource(path.name, resource)
        registry = registry.with_resource(f"./{path.name}", resource)
        if "$id" in schema:
            registry = registry.with_resource(schema["$id"], resource)
    return registry


def validate_instance(instance: dict[str, Any], schema_filename: str) -> None:
    schema_path = SCHEMA_DIR / schema_filename
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(
        schema,
        registry=_build_registry(),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        messages = []
        for error in errors[:5]:
            path = ".".join(str(part) for part in error.path) or "<root>"
            messages.append(f"{path}: {error.message}")
        raise PacketValidationError("; ".join(messages))
