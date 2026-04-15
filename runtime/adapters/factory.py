from __future__ import annotations

from .interfaces import ProviderError
from .memory_providers import (
    DisabledCacheProvider,
    LiveMemoryRetrievalProvider,
    MemoryCacheProvider,
    ReplayRetrievalProvider,
)
from .provider_registry import resolve_provider_config


def create_retrieval_provider(normalized: dict):
    execution_mode = normalized["execution_mode"]

    if execution_mode == "replay":
        return ReplayRetrievalProvider()

    resolved_config = resolve_provider_config(normalized)
    provider_id = resolved_config.get("provider_id", "live_memory")
    if provider_id != "live_memory":
        raise ProviderError("unsupported retrieval provider")

    corpus = resolved_config.get("live_corpus", [])
    return LiveMemoryRetrievalProvider(corpus=corpus)


def create_cache_provider(normalized: dict):
    resolved_config = resolve_provider_config(normalized)
    cache_provider_id = resolved_config.get("cache_provider_id", "memory_cache")
    if not normalized.get("cache_enabled", True):
        return DisabledCacheProvider()
    if cache_provider_id == "disabled_cache":
        return DisabledCacheProvider()
    if cache_provider_id == "memory_cache":
        return MemoryCacheProvider()
    raise ProviderError("unsupported cache provider")
