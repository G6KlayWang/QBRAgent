from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .api_client import SymmonsAPIClient
from .postman_index import PostmanCollectionIndex


TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_property_groups",
            "description": (
                "Retrieve a paginated list of property groups for the current user. "
                "Use filters such as groupType, searchTerm, page, size, or sort when needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "group_type": {
                        "type": "integer",
                        "description": "Numeric group type identifier.",
                    },
                    "search_term": {
                        "type": "string",
                        "description": "Text search filter for property groups.",
                    },
                    "page": {
                        "type": "integer",
                        "description": "Zero-based page index to fetch.",
                        "default": 0,
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of results per page (max 100).",
                        "default": 20,
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort expression, i.e. 'name,asc'.",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_property_group",
            "description": "Fetch metadata for a specific property group using its numeric ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "integer",
                        "description": "Property group identifier.",
                    }
                },
                "required": ["group_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_property",
            "description": (
                "Retrieve rich information about a property, including infrastructure, "
                "contacts, counts, and configuration values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "integer",
                        "description": "Property identifier.",
                    }
                },
                "required": ["property_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_water_roi",
            "description": (
                "Get the list of water ROI annotations associated with a specific property ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "integer",
                        "description": "Property identifier used to retrieve ROI entries.",
                    }
                },
                "required": ["property_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_symmons_endpoint",
            "description": (
                "Invoke any Symmons API endpoint by specifying the HTTP method and path. "
                "Use this for endpoints that are not covered by dedicated tools."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, PATCH, or DELETE).",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    },
                    "path": {
                        "type": "string",
                        "description": "Relative API path beginning with /api.",
                    },
                    "query": {
                        "type": "object",
                        "description": "Optional query string key/value pairs.",
                        "additionalProperties": {"type": ["string", "number", "boolean"]},
                    },
                    "body": {
                        "type": "object",
                        "description": "Optional JSON payload for POST/PUT/PATCH calls.",
                    },
                },
                "required": ["method", "path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_postman_endpoints",
            "description": (
                "Search the bundled Postman collection for endpoint definitions that "
                "match the provided keywords."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords describing the desired endpoint.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of matches to return (default 5).",
                        "default": 5,
                    },
                    "method": {
                        "type": "string",
                        "description": "Optional HTTP method filter.",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    },
                    "folder_contains": {
                        "type": "string",
                        "description": "Optional folder substring to scope the search.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]


class SymmonsToolset:
    """Callable wrappers around Symmons API endpoints."""

    def __init__(
        self,
        api_client: SymmonsAPIClient,
        *,
        postman_collection_path: Optional[str] = None,
    ) -> None:
        self._client = api_client
        self._postman_index: Optional[PostmanCollectionIndex] = None
        if postman_collection_path:
            self._postman_index = PostmanCollectionIndex(
                Path(postman_collection_path).expanduser().resolve()
            )

    def list_property_groups(
        self,
        group_type: Optional[int] = None,
        search_term: Optional[str] = None,
        page: int = 0,
        size: int = 20,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        filters: Dict[str, Any] = {"page": page, "size": size}
        if group_type is not None:
            filters["groupType"] = group_type
        if search_term:
            filters["searchTerm"] = search_term
        if sort:
            filters["sort"] = sort
        return self._client.list_property_groups(**filters)

    def get_property_group(self, group_id: int) -> Dict[str, Any]:
        return self._client.get_property_group(group_id)

    def get_property(self, property_id: int) -> Dict[str, Any]:
        return self._client.get_property(property_id)

    def list_water_roi(self, property_id: int) -> Dict[str, Any]:
        return self._client.list_water_roi(property_id)

    def call_symmons_endpoint(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._client.call_endpoint(
            method=method,
            path=path,
            params=query,
            json_payload=body,
        )

    def search_postman_endpoints(
        self,
        query: str,
        limit: int = 5,
        method: Optional[str] = None,
        folder_contains: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self._postman_index:
            raise ValueError("Postman collection not configured for this agent.")
        return self._postman_index.search_endpoints(
            query=query,
            limit=limit,
            method=method,
            folder_contains=folder_contains,
        )

    def registry(self) -> Dict[str, Callable[..., Dict[str, Any]]]:
        return {
            "list_property_groups": self.list_property_groups,
            "get_property_group": self.get_property_group,
            "get_property": self.get_property,
            "list_water_roi": self.list_water_roi,
            "call_symmons_endpoint": self.call_symmons_endpoint,
            "search_postman_endpoints": self.search_postman_endpoints,
        }

    def describe_endpoint(self, tool_name: str, args: Dict[str, Any]) -> Optional[str]:
        if tool_name == "list_property_groups":
            query_map = {
                "group_type": "groupType",
                "search_term": "searchTerm",
                "page": "page",
                "size": "size",
                "sort": "sort",
            }
            params = []
            for arg_key, query_key in query_map.items():
                if arg_key in args and args[arg_key] is not None:
                    params.append(f"{query_key}={args[arg_key]}")
            suffix = f"?{'&'.join(params)}" if params else ""
            return f"/api/v2/property-groups{suffix}"
        if tool_name == "get_property_group":
            group_id = args.get("group_id")
            return f"/api/v2/property-group/{group_id}"
        if tool_name == "get_property":
            property_id = args.get("property_id")
            return f"/api/v2/property/{property_id}"
        if tool_name == "list_water_roi":
            property_id = args.get("property_id")
            return f"/api/v2/water-roi/list/{property_id}"
        if tool_name == "call_symmons_endpoint":
            return args.get("path")
        if tool_name == "search_postman_endpoints":
            return "postman_collection_search"
        return None

    @staticmethod
    def serialize(result: Dict[str, Any]) -> str:
        return json.dumps(result, default=str)
