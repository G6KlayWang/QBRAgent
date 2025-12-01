from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class PostmanEndpoint:
    name: str
    method: str
    path: str
    description: Optional[str]
    folders: List[str]

    def to_dict(self) -> Dict[str, Optional[str]]:
        payload = asdict(self)
        payload["folders"] = list(self.folders)
        return payload


class PostmanCollectionIndex:
    """Lightweight index to query the exported Postman collection."""

    def __init__(self, collection_path: Path) -> None:
        self.collection_path = collection_path
        self._endpoints: List[PostmanEndpoint] = []
        self._loaded = False

    def search_endpoints(
        self,
        query: str,
        *,
        limit: int = 5,
        method: Optional[str] = None,
        folder_contains: Optional[str] = None,
    ) -> Dict[str, object]:
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        if limit <= 0:
            raise ValueError("limit must be > 0")
        self._ensure_loaded()
        terms = [term for term in query.lower().split() if term]
        method_filter = method.upper() if method else None
        folder_filter = folder_contains.lower() if folder_contains else None
        scored: List[tuple[int, PostmanEndpoint]] = []
        for endpoint in self._endpoints:
            if method_filter and endpoint.method != method_filter:
                continue
            if folder_filter and not any(
                folder_filter in folder.lower() for folder in endpoint.folders
            ):
                continue
            haystack = " ".join(
                filter(
                    None,
                    [
                        endpoint.name,
                        endpoint.path,
                        endpoint.description or "",
                        " ".join(endpoint.folders),
                    ],
                )
            ).lower()
            score = 0
            for term in terms:
                occurrences = haystack.count(term)
                if occurrences:
                    score += occurrences * 2
                else:
                    score -= 1
            scored.append((score, endpoint))
        scored.sort(key=lambda item: item[0], reverse=True)
        matches = [endpoint.to_dict() for _, endpoint in scored[:limit]]
        return {
            "query": query,
            "limit": limit,
            "result_count": len(matches),
            "results": matches,
        }

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not self.collection_path.exists():
            raise FileNotFoundError(
                f"Postman collection not found at {self.collection_path}"
            )
        with self.collection_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        items = payload.get("item", [])
        self._endpoints = list(self._collect_endpoints(items, []))
        self._loaded = True

    def _collect_endpoints(
        self, items: Iterable[Dict[str, object]], parents: List[str]
    ) -> Iterable[PostmanEndpoint]:
        for entry in items:
            name = entry.get("name") or ""
            folders = parents + ([name] if name else [])
            children = entry.get("item")
            if isinstance(children, list):
                yield from self._collect_endpoints(children, folders)
                continue
            request = entry.get("request")
            if not isinstance(request, dict):
                continue
            method = str(request.get("method") or "GET").upper()
            description = request.get("description")
            path = self._extract_path(request.get("url"))
            yield PostmanEndpoint(
                name=name,
                method=method,
                path=path,
                description=description if isinstance(description, str) else None,
                folders=parents,
            )

    @staticmethod
    def _extract_path(raw_url: object) -> str:
        if isinstance(raw_url, str):
            return raw_url
        if isinstance(raw_url, dict):
            if isinstance(raw_url.get("raw"), str):
                return raw_url["raw"]
            if isinstance(raw_url.get("path"), list):
                return "/" + "/".join(str(part) for part in raw_url["path"])
        return "unknown"

