from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import traceback

from dotenv import load_dotenv

from agentic_app.agent import AgentRunResult, SymmonsAgent, ToolCallRecord
from agentic_app.api_client import from_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with the Symmons WTW agent or execute the property-group audit workflow."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="User request to send to the agent. If omitted, the requirements-driven workflow runs.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI chat model to use.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=6,
        help="Maximum tool-calling loops allowed for a response.",
    )
    parser.add_argument(
        "--requirements-path",
        default="requirements/property_group_requirements.json",
        help="Path to the JSON file that enumerates metric groups.",
    )
    parser.add_argument(
        "--property-group-id",
        type=int,
        default=None,
        help="Property group identifier to audit. Defaults to the requirements file value.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory where per-group JSON results will be written.",
    )
    parser.add_argument(
        "--group",
        dest="groups",
        action="append",
        help="Restrict the requirements workflow to specific group names. Can be supplied multiple times.",
    )
    return parser.parse_args()


def load_requirements(path: str) -> Dict[str, Any]:
    req_path = Path(path)
    if not req_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {req_path}")
    with req_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "groups" not in data:
        raise ValueError(f"Requirements file {req_path} must contain a 'groups' field.")
    return data


def slugify(value: str) -> str:
    return "".join(
        ch.lower() if ch.isalnum() else "-"
        for ch in value.strip()
    ).strip("-") or "group"


def build_metric_prompt(metric: Dict[str, Any], property_group_id: int) -> str:
    key = metric.get("key")
    label = metric.get("label") or key
    description = metric.get("description", "").strip()
    desc_clause = f" ({description})" if description else ""
    return (
        f"Gather '{label}' (key: {key}){desc_clause} for property group ID {property_group_id}. "
        "Use Postman endpoint search before calling APIs you are not certain about. "
        "Quote the exact value, units, timeframe, and describe the source endpoint."
    )


def build_group_prompt(
    group: Dict[str, Any], property_group_id: int
) -> tuple[str, List[Dict[str, str]]]:
    metrics = group.get("metrics", [])
    metric_prompts: List[Dict[str, str]] = []
    metric_line_items: List[str] = []
    for metric in metrics:
        line = f"- {metric.get('key')}: {metric.get('description')}"
        metric_line_items.append(line)
        metric_prompt = build_metric_prompt(metric, property_group_id)
        metric_prompts.append(
            {
                "key": metric.get("key"),
                "label": metric.get("label"),
                "prompt": metric_prompt,
            }
        )
    metric_line_block = "\n".join(metric_line_items)
    metric_prompt_block = "\n".join(
        f"{idx}. {text['prompt']}" for idx, text in enumerate(metric_prompts, start=1)
    )
    group_prompt = (
        f"You are auditing '{group.get('name')}' metrics for property group ID {property_group_id}.\n"
        "Use the metric-specific prompts below to drive each fetch. "
        "Always search the Postman collection before calling an unfamiliar endpoint, and cite the exact API path.\n\n"
        f"Metrics overview:\n{metric_line_block}\n\n"
        "Metric-specific instructions:\n"
        f"{metric_prompt_block}\n\n"
        "After gathering data for each metric, summarize the findings with values, units, endpoints, and any gaps."
    )
    return group_prompt, metric_prompts


def ensure_output_dir(path: str) -> Path:
    output_path = Path(path)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def summarize_tool_call(result: Any) -> str:
    if result is None:
        return "No data returned."
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result.get('error')}"
        keys = ", ".join(list(result.keys())[:6])
        size_info: List[str] = []
        data = result.get("data")
        if isinstance(data, list):
            size_info.append(f"data_count={len(data)}")
        if isinstance(data, dict):
            size_info.append(f"data_keys={list(data.keys())[:5]}")
        context = "; ".join(filter(None, [keys, ", ".join(size_info)]))
        return context or "Structured response received."
    if isinstance(result, list):
        return f"List with {len(result)} entries."
    if isinstance(result, str):
        return result[:400]
    return str(result)


def build_fetch_summaries(tool_calls: List[ToolCallRecord]) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    for idx, record in enumerate(tool_calls, start=1):
            summaries.append(
            {
                "order": idx,
                "tool_name": record.tool_name,
                "endpoint": record.endpoint,
                "arguments": record.arguments,
                "summary": summarize_tool_call(record.result),
                "raw_result": record.result,
            }
        )
    return summaries


def write_group_result(
    group: Dict[str, Any],
    prompt: str,
    property_group_id: int,
    result: AgentRunResult,
    output_dir: Path,
    index: int,
    metric_prompts: List[Dict[str, str]],
) -> Path:
    timestamp = datetime.now(timezone.utc).isoformat()
    fetch_summaries = build_fetch_summaries(result.tool_calls)
    payload: Dict[str, Any] = {
        "group_order": index,
        "group_name": group.get("name"),
        "property_group_id": property_group_id,
        "prompt": prompt,
        "metrics": group.get("metrics", []),
        "metric_prompts": metric_prompts,
        "agent_summary": result.reply,
        "fetches": fetch_summaries,
        "tool_calls": [record.to_dict() for record in result.tool_calls],
        "completed_at": timestamp,
    }
    slug = slugify(group.get("name", f"group-{index}")) or f"group-{index}"
    file_path = output_dir / f"{index:02d}-{slug}.json"
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return file_path


def run_requirements_workflow(
    agent: SymmonsAgent,
    requirements_path: str,
    property_group_id: Optional[int],
    output_dir: str,
    group_name_filters: Optional[List[str]] = None,
) -> List[Path]:
    requirements = load_requirements(requirements_path)
    resolved_group_id = property_group_id or requirements.get("property_group_id_default")
    if resolved_group_id is None:
        raise ValueError(
            "A property group ID must be provided via --property-group-id or in the requirements file."
        )
    groups = requirements.get("groups", [])
    if not groups:
        raise ValueError("Requirements file does not define any groups.")
    filtered_groups = groups
    if group_name_filters:
        normalized_filters = {name.strip().lower() for name in group_name_filters}
        filtered_groups = [
            group for group in groups if str(group.get("name", "")).lower() in normalized_filters
        ]
        if not filtered_groups:
            raise ValueError(
                "No requirement groups matched the provided --group filters. "
                f"Available groups: {[group.get('name') for group in groups]}"
            )
    destination = ensure_output_dir(output_dir)
    written_files: List[Path] = []
    for idx, group in enumerate(filtered_groups, start=1):
        prompt, metric_prompts = build_group_prompt(group, resolved_group_id)
        try:
            result = agent.run(prompt)
        except Exception as exc:
            tb = traceback.format_exc()
            print(
                f"Group '{group.get('name')}' failed: {exc}",
                file=sys.stderr,
            )
            print(tb, file=sys.stderr)
            result = AgentRunResult(
                reply=f"Failed to complete '{group.get('name')}' request: {exc}\n{tb}",
                tool_calls=[],
                messages=[],
            )
        file_path = write_group_result(
            group=group,
            prompt=prompt,
            property_group_id=resolved_group_id,
            result=result,
            output_dir=destination,
            index=idx,
            metric_prompts=metric_prompts,
        )
        written_files.append(file_path)
    return written_files


def main() -> int:
    load_dotenv()
    args = parse_args()
    api_client = from_env()
    agent = SymmonsAgent(
        api_client,
        model=args.model,
        max_turns=args.max_turns,
    )

    prompt: Optional[str] = args.prompt
    if prompt is None and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    if prompt:
        try:
            result = agent.run(prompt)
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"Agent failed: {exc}", file=sys.stderr)
            print(tb, file=sys.stderr)
            return 1
        print(result.reply)
        return 0

    generated_files = run_requirements_workflow(
        agent=agent,
        requirements_path=args.requirements_path,
        property_group_id=args.property_group_id,
        output_dir=args.output_dir,
        group_name_filters=args.groups,
    )
    print("Completed requirements workflow. Generated files:")
    for file_path in generated_files:
        print(f"- {file_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
