import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
  from dotenv import load_dotenv
except ImportError:
  load_dotenv = None


def load_env() -> None:
  if load_dotenv:
    load_dotenv()


def read_json(path: Path) -> Dict[str, Any]:
  with path.open("r", encoding="utf-8") as f:
    return json.load(f)


def read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def percent_change(current: float, previous: float) -> float | None:
  if previous in (0, None):
    return None
  return round(((current - previous) / previous) * 100, 1)


def aggregate_property(property_data: Dict[str, Any], quarter_id: str) -> Dict[str, Any]:
  totals_current = {"financial": 0, "water": 0, "energy": 0, "downtime": 0, "investment": 0}
  totals_previous = {"financial": 0, "water": 0, "energy": 0, "downtime": 0, "investment": 0}
  hotels_payload: List[Dict[str, Any]] = []

  for hotel_id, hotel in property_data.get("hotels", {}).items():
    if quarter_id not in hotel["quarters"]:
      continue
    quarter_keys = sorted(hotel["quarters"].keys(), reverse=True)
    if quarter_id not in quarter_keys:
      continue
    idx = quarter_keys.index(quarter_id)
    if idx == len(quarter_keys) - 1:
      continue  # no previous quarter to compare
    prev_q = quarter_keys[idx + 1]
    current = hotel["quarters"][quarter_id]["metrics"]
    previous = hotel["quarters"][prev_q]["metrics"]

    totals_current["financial"] += current["total_financial_impact_usd"]
    totals_current["water"] += current["water_cost_avoided_usd"]
    totals_current["energy"] += current["energy_cost_avoided_usd"]
    totals_current["downtime"] += current["downtime_cost_avoided_usd"]
    totals_current["investment"] += current["total_investment_to_date_usd"]

    totals_previous["financial"] += previous["total_financial_impact_usd"]
    totals_previous["water"] += previous["water_cost_avoided_usd"]
    totals_previous["energy"] += previous["energy_cost_avoided_usd"]
    totals_previous["downtime"] += previous["downtime_cost_avoided_usd"]
    totals_previous["investment"] += previous["total_investment_to_date_usd"]

    hotels_payload.append(
      {
        "hotel_name": hotel["hotel_name"],
        "current_quarter": hotel["quarters"][quarter_id]["label"],
        "previous_quarter": hotel["quarters"][prev_q]["label"],
        "metrics_current": current,
        "metrics_previous": previous,
        "deltas_pct": {
          "total": percent_change(current["total_financial_impact_usd"], previous["total_financial_impact_usd"]),
          "water": percent_change(current["water_cost_avoided_usd"], previous["water_cost_avoided_usd"]),
          "energy": percent_change(current["energy_cost_avoided_usd"], previous["energy_cost_avoided_usd"]),
          "downtime": percent_change(current["downtime_cost_avoided_usd"], previous["downtime_cost_avoided_usd"]),
        },
        "phase2_option": hotel.get("phase2_option", {}),
      }
    )

  aggregate = {
    "totals": totals_current,
    "totals_previous": totals_previous,
    "deltas_pct": {
      "total": percent_change(totals_current["financial"], totals_previous["financial"]),
      "water": percent_change(totals_current["water"], totals_previous["water"]),
      "energy": percent_change(totals_current["energy"], totals_previous["energy"]),
      "downtime": percent_change(totals_current["downtime"], totals_previous["downtime"]),
    },
    "roi_multiple_to_date": round(totals_current["financial"] / totals_current["investment"], 2) if totals_current["investment"] else None,
  }

  return {"aggregate": aggregate, "hotels": hotels_payload}


def build_prompt(template_html: str, property_data: Dict[str, Any], property_name: str, quarter_id: str) -> str:
  agg_payload = aggregate_property(property_data, quarter_id)
  hotels_payload = agg_payload["hotels"]
  if not hotels_payload:
    raise SystemExit("No hotels with both current and previous quarter data found.")

  aggregate = agg_payload["aggregate"]

  instructions = """
You are generating a completed HTML QBR using the provided template.
Rules:
- Keep the HTML structure and CSS from the template; replace placeholders with real content.
- Build a portfolio-level executive summary (3-5 sentences), decline acknowledgement (>10% declines), top takeaways, ROI snapshot, critical decision, and next steps.
- Include hotel-level summaries for each hotel provided (opening statement, decline ack if needed, top takeaways, ROI snapshot, critical decision, next steps).
- Tone: business/financial, concise, persona-aware (CFO/owner focus). Avoid raw telemetry.
- Critical decisions must be generated from metrics and phase2_option, not copied verbatim.
- Return ONLY the final HTML with placeholders filled.

Placeholders:
- {{QUARTER}} -> current quarter label
- {{PROPERTY_NAME}} -> property/portfolio name
- {{PORTFOLIO_IMPACT}} -> headline total financial impact (formatted currency)
- {{PROPERTY_OPENING_STATEMENT}} -> 3-5 sentence executive summary
- {{PROPERTY_DECLINE_ACK}} -> explicit note if any key metric declined >10% QoQ (explain)
- {{PROPERTY_TOP_TAKEAWAYS}} -> <li> items
- {{PROPERTY_ROI_SNAPSHOT}} -> HTML using .metric-grid/.metric classes; include totals and deltas
- {{PROPERTY_CRITICAL_DECISION}} -> concise ask (deadline, capex, savings range)
- {{PROPERTY_NEXT_STEPS}} -> bullets or paragraphs
- {{HOTEL_SECTIONS}} -> repeated hotel blocks with structure matching the template card (include ROI and critical decision per hotel)
"""

  data_context = {
    "property_name": property_name,
    "quarter": quarter_id,
    "aggregate": aggregate,
    "hotels": hotels_payload,
  }

  return f"""{instructions}

TEMPLATE_HTML:
{template_html}

DATA_JSON:
{json.dumps(data_context, indent=2)}

Return the final HTML with all placeholders replaced.
"""


def call_openai(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.35) -> str:
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set in environment.")

  payload = {
    "model": model,
    "temperature": temperature,
    "messages": [
      {
        "role": "system",
        "content": "You fill HTML templates for QBRs. Respond ONLY with the completed HTML. Do not include any other text.",
      },
      {"role": "user", "content": prompt},
    ],
  }

  data_bytes = json.dumps(payload).encode("utf-8")
  req = Request(
    "https://api.openai.com/v1/chat/completions",
    data=data_bytes,
    headers={
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}",
    },
  )

  try:
    with urlopen(req) as resp:
      resp_body = resp.read()
  except HTTPError as e:
    detail = e.read().decode()
    raise RuntimeError(f"OpenAI HTTPError {e.code}: {detail}") from e
  except URLError as e:
    raise RuntimeError(f"OpenAI URLError: {e.reason}") from e

  parsed = json.loads(resp_body)
  content = parsed.get("choices", [{}])[0].get("message", {}).get("content")
  if not content:
    raise RuntimeError("Empty response from OpenAI")
  return content


def write_output(html: str, dest: Path) -> None:
  dest.parent.mkdir(parents=True, exist_ok=True)
  dest.write_text(html, encoding="utf-8")


def main() -> None:
  load_env()

  parser = argparse.ArgumentParser(description="Generate portfolio QBR HTML via OpenAI.")
  parser.add_argument("--property", dest="property_id", default="hilton_regional_portfolio", help="Property ID")
  parser.add_argument("--quarter", dest="quarter_id", default="2025-Q3", help="Quarter ID (e.g., 2025-Q3)")
  parser.add_argument("--data", dest="data_path", default="data.json", help="Path to data JSON")
  parser.add_argument("--template", dest="template_path", default="template.html", help="Path to HTML template")
  parser.add_argument("--output", dest="output_path", default="dist/report.html", help="Output HTML file")
  parser.add_argument("--model", dest="model", default="gpt-4o-mini", help="OpenAI model")
  parser.add_argument("--temperature", dest="temperature", type=float, default=0.35, help="Sampling temperature")
  args = parser.parse_args()

  data = read_json(Path(args.data_path))
  template_html = read_text(Path(args.template_path))

  try:
    property_data = data["properties"][args.property_id]
  except KeyError as e:
    raise SystemExit(f"Missing data for selection: {e}")

  prompt = build_prompt(template_html, property_data, property_data.get("name", args.property_id), args.quarter_id)
  html = call_openai(prompt, model=args.model, temperature=args.temperature)
  write_output(html, Path(args.output_path))
  print(f"Report generated at {args.output_path}")


if __name__ == "__main__":
  main()
