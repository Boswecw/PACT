from __future__ import annotations

from .interfaces import ProviderError


def resolve_provider_config(normalized: dict) -> dict:
    adapter_config = dict(normalized.get("adapter_config", {}))
    provider_ref = adapter_config.get("provider_ref")
    if not provider_ref:
        return adapter_config

    registry = adapter_config.get("provider_registry", {})
    if not isinstance(registry, dict):
        raise ProviderError("provider_registry must be an object")
    resolved = registry.get(provider_ref)
    if not isinstance(resolved, dict):
        raise ProviderError("provider_ref not found in provider_registry")
    merged = dict(resolved)
    for key, value in adapter_config.items():
        if key in {"provider_registry", "provider_ref"}:
            continue
        merged[key] = value
    return merged
