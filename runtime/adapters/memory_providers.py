from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .interfaces import CacheProvider, ProviderError, RetrievalProvider


_MEMORY_CACHE: dict[str, Any] = {}


@dataclass
class ReplayRetrievalProvider(RetrievalProvider):
    provider_id: str = "replay_passthrough"

    def search(self, query: str, request: dict[str, Any]) -> list[dict[str, Any]]:
        return list(request.get("retrieval_input", []))


@dataclass
class LiveMemoryRetrievalProvider(RetrievalProvider):
    corpus: list[dict[str, Any]]
    provider_id: str = "live_memory"

    def search(self, query: str, request: dict[str, Any]) -> list[dict[str, Any]]:
        normalized_query = (query or "").strip().lower()
        if not self.corpus:
            raise ProviderError("live corpus is unavailable")
        if not normalized_query:
            return list(self.corpus[:5])

        terms = [term for term in normalized_query.split() if term]
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in self.corpus:
            haystack = f"{item.get('title', '')} {item.get('content', '')}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score > 0:
                enriched = dict(item)
                enriched["lexical_score"] = max(float(item.get("lexical_score", 0.0)), float(score))
                scored.append((score, enriched))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        if scored:
            return [item for _, item in scored]

        # fallback: return first small bounded set so the engine can still decide grounding posture
        return list(self.corpus[:3])


@dataclass
class MemoryCacheProvider(CacheProvider):
    provider_id: str = "memory_cache"

    def get(self, key: str) -> Any | None:
        return _MEMORY_CACHE.get(key)

    def set(self, key: str, value: Any) -> None:
        _MEMORY_CACHE[key] = value


@dataclass
class DisabledCacheProvider(CacheProvider):
    provider_id: str = "disabled_cache"

    def get(self, key: str) -> Any | None:
        raise ProviderError("cache provider unavailable")

    def set(self, key: str, value: Any) -> None:
        raise ProviderError("cache provider unavailable")
