"""
Agent-driven pipeline to push JSON data into the QBR HTML/React template.

Usage:
    OPENAI_API_KEY=... python services/report_agent.py

- Reads raw metrics from report_data.json.
- Uses the OpenAI Agent SDK to craft narratives.
- Writes a UI-ready JSON payload to report_output.json (consumed by App.tsx).
- Asks the Agent to merge the payload into report_template.html and saves generated_report.html.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR / "report_data.json"
OUTPUT_DATA_PATH = BASE_DIR / "report_output.json"
HTML_TEMPLATE_PATH = BASE_DIR / "report_template.html"
FILLED_HTML_PATH = BASE_DIR / "generated_report.html"


def _quarter_label(key: str) -> str:
    if "-" in key:
        year, quarter = key.split("-", 1)
        return f"{quarter} {year}"
    return key


def _aggregate_metrics(hotels: List[Dict[str, Any]], metrics_key: str) -> Dict[str, Any]:
    totals: Dict[str, Any] = {
        "total_financial_impact_usd": 0,
        "water_cost_avoided_usd": 0,
        "energy_cost_avoided_usd": 0,
        "downtime_cost_avoided_usd": 0,
        "total_investment_to_date_usd": 0,
        "roi_multiple_to_date": 0,
        "alert_ack_within_4h_pct": 0,
        "high_priority_resolution_lt_6h_pct": 0,
        "payback_status": "in_progress",
        "payback_achieved_month": None,
    }

    count = 0
    roi_sum = 0.0
    for hotel in hotels:
        metrics = hotel.get(metrics_key, {})
        count += 1
        totals["total_financial_impact_usd"] += metrics.get("total_financial_impact_usd", 0)
        totals["water_cost_avoided_usd"] += metrics.get("water_cost_avoided_usd", 0)
        totals["energy_cost_avoided_usd"] += metrics.get("energy_cost_avoided_usd", 0)
        totals["downtime_cost_avoided_usd"] += metrics.get("downtime_cost_avoided_usd", 0)
        totals["total_investment_to_date_usd"] += metrics.get("total_investment_to_date_usd", 0)
        roi_sum += metrics.get("roi_multiple_to_date", 0)
        totals["alert_ack_within_4h_pct"] += metrics.get("alert_ack_within_4h_pct", 0)
        totals["high_priority_resolution_lt_6h_pct"] += metrics.get("high_priority_resolution_lt_6h_pct", 0)

    if count:
        totals["roi_multiple_to_date"] = round(roi_sum / count, 2)
        totals["alert_ack_within_4h_pct"] = round(totals["alert_ack_within_4h_pct"] / count)
        totals["high_priority_resolution_lt_6h_pct"] = round(totals["high_priority_resolution_lt_6h_pct"] / count)
        totals["payback_status"] = "achieved" if totals["roi_multiple_to_date"] >= 1 else "in_progress"

    return totals


def _extract_text(response: Any) -> str:
    # Agents API returns output segments; this helper keeps parsing defensive.
    direct = getattr(response, "output_text", None)
    if direct:
        return direct
    if getattr(response, "output", None):
        for item in response.output:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    return text
    if hasattr(response, "choices"):
        # Fallback for chat-like responses
        return response.choices[0].message["content"]  # type: ignore
    raise RuntimeError("Agent response did not contain text output")


def _extract_json(response: Any) -> Dict[str, Any]:
    text = _extract_text(response)
    return json.loads(text)


def _create_agent(client: OpenAI):
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    return client.agents.create(
        name="QBR HTML Autofill Agent",
        instructions=(
            "You are a chief strategy officer tone assistant. "
            "Given quarterly hotel metrics you produce concise narrative copy and fill HTML templates. "
            "Keep the styling and classes intact while replacing placeholders with data."
        ),
        model=model,
    )


def _generate_narrative(client: OpenAI, agent_id: str, model: str, *, entity_name: str, current: Dict[str, Any], previous: Dict[str, Any], phase2: Dict[str, Any]) -> Dict[str, Any]:
    prompt = (
        "Create JSON for a QBR narrative. "
        "Fields: headline, opening_statement_primary, top_5_takeaways (5 bullet strings), "
        "critical_decision_narrative, next_steps (3 objects with description and optional date). "
        f"Entity: {entity_name}\n"
        f"Current quarter metrics: {json.dumps(current)}\n"
        f"Previous quarter metrics: {json.dumps(previous)}\n"
        f"Phase 2 option: {json.dumps(phase2)}\n"
        "Tone: premium, concise, and executive-ready. Do not add markdown."
    )
    response = client.responses.create(
        model=model,
        agent_id=agent_id,
        response_format={"type": "json_object"},
        input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
    )
    return _extract_json(response)


def _build_payload(client: OpenAI, agent_id: str, model: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    current_q = raw["current_quarter"]
    prev_q = raw["previous_quarter"]
    quarter_label = _quarter_label(current_q)

    output: Dict[str, Any] = {"properties": {}}
    for prop in raw.get("properties", []):
        hotels_output: Dict[str, Any] = {}
        current_portfolio_metrics = _aggregate_metrics(prop["hotels"], "current_metrics")
        prev_portfolio_metrics = _aggregate_metrics(prop["hotels"], "previous_metrics")

        portfolio_narrative = _generate_narrative(
            client,
            agent_id,
            model,
            entity_name=prop["name"],
            current=current_portfolio_metrics,
            previous=prev_portfolio_metrics,
            phase2={"hotels": [h.get("phase2_option", {}) for h in prop["hotels"]]},
        )

        for hotel in prop.get("hotels", []):
            narrative = _generate_narrative(
                client,
                agent_id,
                model,
                entity_name=hotel["hotel_name"],
                current=hotel["current_metrics"],
                previous=hotel["previous_metrics"],
                phase2=hotel.get("phase2_option", {}),
            )

            hotels_output[hotel["id"]] = {
                "hotel_name": hotel["hotel_name"],
                "current_quarter": current_q,
                "quarters": {
                    current_q: {"label": quarter_label, "metrics": hotel["current_metrics"]},
                    prev_q: {"label": _quarter_label(prev_q), "metrics": hotel["previous_metrics"]},
                },
                "phase2_option": hotel.get("phase2_option", {}),
                "narrative": narrative,
            }

        output["properties"][prop["id"]] = {
            "name": prop["name"],
            "hotels": hotels_output,
            "portfolio_narrative": portfolio_narrative,
        }
    return output


def _render_html(client: OpenAI, agent_id: str, model: str, template: str, payload: Dict[str, Any], quarter_label: str) -> str:
    prompt = (
        "You are filling the provided Tailwind HTML template for a QBR report. "
        "Duplicate the <section> with class 'break-after-page' for the portfolio overview and for each hotel in the payload. "
        "Replace placeholder tokens like {{title}}, {{headline}}, {{takeaway_one}} with real values. "
        "Use USD formatting with commas and keep the existing design untouched.\n\n"
        f"Quarter label for the report header: {quarter_label}\n"
        f"Template:\n{template}\n\n"
        f"Payload JSON:\n{json.dumps(payload)}\n\n"
        "Return only the final HTML text with all placeholders replaced; do not include additional explanations."
    )
    response = client.responses.create(
        model=model,
        agent_id=agent_id,
        input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
    )
    return _extract_text(response)


def main():
    parser = argparse.ArgumentParser(description="Fill report data with the OpenAI Agent SDK.")
    parser.add_argument("--api-key", dest="api_key", help="OpenAI API key (falls back to OPENAI_API_KEY).")
    parser.add_argument("--skip-html", action="store_true", help="Only generate report_output.json without HTML.")
    args = parser.parse_args()

    # Load .env so OPENAI_API_KEY can be set there.
    load_dotenv()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required.")

    raw_payload = json.loads(RAW_DATA_PATH.read_text())
    client = OpenAI(api_key=api_key)
    agent = _create_agent(client)

    model_used = getattr(agent, "model", os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    report_payload = _build_payload(client, agent.id, model_used, raw_payload)
    OUTPUT_DATA_PATH.write_text(json.dumps(report_payload, indent=2))
    print(f"Report data written to {OUTPUT_DATA_PATH}")

    if args.skip_html:
        return

    template_html = HTML_TEMPLATE_PATH.read_text()
    quarter_label = _quarter_label(raw_payload["current_quarter"])
    filled_html = _render_html(client, agent.id, model_used, template_html, report_payload, quarter_label)
    FILLED_HTML_PATH.write_text(filled_html)
    print(f"Filled HTML written to {FILLED_HTML_PATH}")


if __name__ == "__main__":
    main()
