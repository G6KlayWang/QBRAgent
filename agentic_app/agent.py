from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI

from .api_client import SymmonsAPIClient
from .tools import SymmonsToolset, TOOL_DEFINITIONS


DEFAULT_SYSTEM_PROMPT = (
    "You are SymmonsAI, an assistant that audits Symmons WTW property performance. "
    "Use the provided tools to look up metrics, and consult the Postman collection "
    "search tool whenever you need to confirm which endpoint exposes specific data. "
    "Always explain what data was found, cite concrete values, and list any metrics "
    "that could not be located so a follow-up action can be taken."
)


@dataclass
class ToolCallRecord:
    tool_name: str
    arguments: Dict[str, Any]
    endpoint: Optional[str]
    result: Any

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "endpoint": self.endpoint,
            "result": self.result,
        }


@dataclass
class AgentRunResult:
    reply: str
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reply": self.reply,
            "tool_calls": [record.to_dict() for record in self.tool_calls],
            "messages": self.messages,
        }


class SymmonsAgent:
    """OpenAI function-calling loop wired to the Symmons API toolset."""

    def __init__(
        self,
        api_client: SymmonsAPIClient,
        *,
        llm: Optional[ChatOpenAI] = None,
        model: Optional[str] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_turns: int = 6,
        postman_collection_path: Optional[str] = None,
    ) -> None:
        self.api_client = api_client
        resolved_postman_path = self._resolve_postman_path(postman_collection_path)
        self.toolset = SymmonsToolset(
            api_client,
            postman_collection_path=resolved_postman_path,
        )
        self.tool_registry = self.toolset.registry()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if llm:
            self.llm = llm
        else:
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=0,
            )
        self.llm_with_tools = self.llm.bind_tools(TOOL_DEFINITIONS)
        self.system_prompt = system_prompt
        self.max_turns = max_turns

    def run(
        self,
        user_prompt: str,
        *,
        conversation: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> AgentRunResult:
        messages: List[BaseMessage] = [SystemMessage(content=self.system_prompt)]
        if conversation:
            messages.extend(self._convert_history(conversation))
        messages.append(HumanMessage(content=user_prompt))
        tool_call_log: List[ToolCallRecord] = []

        for _ in range(self.max_turns):
            ai_message = self.llm_with_tools.invoke(messages)
            messages.append(ai_message)
            tool_calls = self._extract_tool_calls(ai_message)
            if tool_calls:
                for call in tool_calls:
                    function_block = call.get("function") or {}
                    tool_name = function_block.get("name") or call.get("name")
                    arguments = function_block.get("arguments") or call.get("arguments")
                    if not tool_name:
                        continue
                    parsed_args, result_obj, serialized = self._dispatch_tool_call(
                        tool_name,
                        arguments,
                    )
                    tool_call_log.append(
                        ToolCallRecord(
                            tool_name=tool_name,
                            arguments=parsed_args,
                            endpoint=self.toolset.describe_endpoint(
                                tool_name, parsed_args
                            ),
                            result=result_obj,
                        )
                    )
                    messages.append(
                        ToolMessage(
                            content=serialized,
                            tool_call_id=call.get("id"),
                            name=tool_name,
                        )
                    )
                continue
            text_reply = self._normalize_response_content(ai_message)
            if text_reply:
                return AgentRunResult(
                    reply=text_reply,
                    tool_calls=tool_call_log,
                    messages=self._serialize_messages(messages),
                )

        raise RuntimeError("Agent reached max turns without producing a reply.")

    def _dispatch_tool_call(
        self,
        name: str,
        arguments: Any,
    ) -> tuple[Dict[str, Any], Any, str]:
        if name not in self.tool_registry:
            error = {"error": f"Unknown tool '{name}'"}
            return {}, error, json.dumps(error)
        parsed_args: Dict[str, Any]
        try:
            if arguments is None:
                parsed_args = {}
            elif isinstance(arguments, str):
                parsed_args = json.loads(arguments or "{}")
            elif isinstance(arguments, dict):
                parsed_args = arguments
            else:
                parsed_args = json.loads(str(arguments))
        except json.JSONDecodeError as exc:
            error = {"error": f"Invalid arguments for {name}: {exc}"}
            return {}, error, json.dumps(error)
        try:
            result = self.tool_registry[name](**parsed_args)
        except Exception as exc:  # noqa: BLE001 - surface tool exceptions
            error = {"error": str(exc)}
            return parsed_args, error, json.dumps(error)
        serialized = SymmonsToolset.serialize(result)
        return parsed_args, result, serialized

    @staticmethod
    def _extract_tool_calls(message: AIMessage) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        seen_ids: set[str] = set()
        raw_calls = getattr(message, "tool_calls", None)
        sources = []
        if raw_calls:
            sources.append(raw_calls)
        legacy_calls = message.additional_kwargs.get("tool_calls")
        if legacy_calls:
            sources.append(legacy_calls)
        for source in sources:
            for call in source:
                call_id: Optional[str]
                call_type: Optional[str]
                if isinstance(call, dict):
                    call_id = call.get("id")
                    call_type = call.get("type")
                    if call_id and call_id in seen_ids:
                        continue
                    normalized.append(
                        {
                            "id": call_id,
                            "type": call_type,
                            "function": call.get("function")
                            or {
                                "name": call.get("name"),
                                "arguments": call.get("arguments"),
                            },
                        }
                    )
                    if call_id:
                        seen_ids.add(call_id)
                    continue
                entry: Dict[str, Any] = {
                    "id": getattr(call, "id", None),
                    "type": getattr(call, "type", None),
                }
                call_id = entry["id"]
                if isinstance(call_id, str) and call_id in seen_ids:
                    continue
                function = getattr(call, "function", None)
                if isinstance(function, dict):
                    entry["function"] = function
                else:
                    entry["function"] = {
                        "name": (
                            getattr(function, "name", None)
                            if function is not None
                            else getattr(call, "name", None)
                        ),
                        "arguments": (
                            getattr(function, "arguments", None)
                            if function is not None
                            else getattr(call, "arguments", None)
                        ),
                    }
                normalized.append(entry)
                if isinstance(call_id, str):
                    seen_ids.add(call_id)
        return normalized

    @staticmethod
    def _normalize_response_content(message: AIMessage) -> str:
        content = message.content
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            return "\n".join(part for part in text_parts if part).strip()
        return ""

    @staticmethod
    def _convert_history(
        conversation: Iterable[Dict[str, Any]]
    ) -> List[BaseMessage]:
        converted: List[BaseMessage] = []
        for entry in conversation:
            role = entry.get("role")
            content = entry.get("content", "")
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "user":
                converted.append(HumanMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            elif role == "tool":
                tool_call_id = entry.get("tool_call_id") or str(uuid4())
                converted.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id,
                        name=entry.get("name"),
                    )
                )
        return converted

    @staticmethod
    def _serialize_messages(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        serialized: List[Dict[str, Any]] = []
        for message in messages:
            entry: Dict[str, Any] = {
                "type": message.type,
                "content": message.content,
            }
            if isinstance(message, ToolMessage):
                entry["tool_call_id"] = message.tool_call_id
                if message.name:
                    entry["name"] = message.name
            if isinstance(message, AIMessage):
                tool_calls = message.additional_kwargs.get("tool_calls")
                if tool_calls:
                    entry["tool_calls"] = tool_calls
            if message.additional_kwargs:
                entry.setdefault("additional_kwargs", message.additional_kwargs)
            serialized.append(entry)
        return serialized

    @staticmethod
    def _resolve_postman_path(
        explicit_path: Optional[str],
    ) -> Optional[str]:
        candidate = explicit_path or os.getenv("SYM_POSTMAN_PATH")
        if candidate:
            return str(Path(candidate).expanduser().resolve())
        repo_root = Path(__file__).resolve().parents[1]
        fallback = repo_root / "SymmonsWTWAPI.postman_collection"
        if fallback.exists():
            return str(fallback)
        return None
