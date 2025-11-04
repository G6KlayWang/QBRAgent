from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from .api_client import SymmonsAPIClient


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
]


class SymmonsToolset:
    """Callable wrappers around Symmons API endpoints."""

    def __init__(self, api_client: SymmonsAPIClient) -> None:
        self._client = api_client

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

    def registry(self) -> Dict[str, Callable[..., Dict[str, Any]]]:
        return {
            "list_property_groups": self.list_property_groups,
            "get_property_group": self.get_property_group,
            "get_property": self.get_property,
            "list_water_roi": self.list_water_roi,
        }

    @staticmethod
    def serialize(result: Dict[str, Any]) -> str:
        return json.dumps(result, default=str)

