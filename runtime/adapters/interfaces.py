from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class RetrievalProvider(Protocol):
    provider_id: str

    def search(self, query: str, request: dict[str, Any]) -> list[dict[str, Any]]:
        ...


class CacheProvider(Protocol):
    provider_id: str

    def get(self, key: str) -> Any | None:
        ...

    def set(self, key: str, value: Any) -> None:
        ...


@dataclass
class ProviderError(Exception):
    message: str
    public_reason_code: str = "validation_failed"
    failure_state: str = "compiler_failure"

    def __str__(self) -> str:
        return self.message
