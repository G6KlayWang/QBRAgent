from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

from openai import OpenAI

from .api_client import SymmonsAPIClient
from .tools import SymmonsToolset, TOOL_DEFINITIONS


DEFAULT_SYSTEM_PROMPT = (
    "You are SymmonsAI, an assistant that answers questions about Symmons WTW data. "
    "Decide when to call tools to retrieve live data, and quote relevant numbers in "
    "your response. When you cannot find information, say so explicitly."
)


class SymmonsAgent:
    """OpenAI function-calling loop wired to the Symmons API toolset."""

    def __init__(
        self,
        api_client: SymmonsAPIClient,
        *,
        openai_client: Optional[OpenAI] = None,
        model: Optional[str] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_turns: int = 6,
    ) -> None:
        self.api_client = api_client
        self.toolset = SymmonsToolset(api_client)
        self.tool_registry = self.toolset.registry()
        self.openai = openai_client or OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5")
        self.system_prompt = system_prompt
        self.max_turns = max_turns

    def run(
        self,
        user_prompt: str,
        *,
        conversation: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> str:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        if conversation:
            messages.extend(list(conversation))
        messages.append({"role": "user", "content": user_prompt})

        for _ in range(self.max_turns):
            completion = self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
            message = completion.choices[0].message
            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_msg["tool_calls"] = []
                for call in message.tool_calls:
                    assistant_msg["tool_calls"].append(
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                    )
                messages.append(assistant_msg)
                for call in message.tool_calls:
                    result = self._dispatch_tool_call(call.function.name, call.function.arguments)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result,
                        }
                    )
                continue
            messages.append(assistant_msg)
            if message.content:
                return message.content

        raise RuntimeError("Agent reached max turns without producing a reply.")

    def _dispatch_tool_call(self, name: str, arguments: Optional[str]) -> str:
        if name not in self.tool_registry:
            return json.dumps({"error": f"Unknown tool '{name}'"})
        try:
            parsed_args = json.loads(arguments or "{}")
        except json.JSONDecodeError as exc:
            return json.dumps({"error": f"Invalid arguments for {name}: {exc}"})
        try:
            result = self.tool_registry[name](**parsed_args)
        except Exception as exc:  # noqa: BLE001 - surface tool exceptions
            return json.dumps({"error": str(exc)})
        return SymmonsToolset.serialize(result)

