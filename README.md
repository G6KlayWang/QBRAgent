# QBR Executive Summary (Static + LLM-optional)

- Interactive QBR viewer with property/hotel/quarter selectors (`index.html`, `render.js`, `elements.js`, `styles.css`) using demo data in `data.js`.
- Optional LLM generation (per-hotel narrative) via a FastAPI proxy in `server.py`; otherwise a deterministic fallback narrative is used.
- Offline/CLI path to generate a fully-populated portfolio HTML from a template via `generate_report.py` (OpenAI API required).

## Project Layout
- `index.html` – entry point for the interactive summary UI.
- `data.js` – demo dataset and per-hotel `llm_config` (set `enabled: true` to call the proxy/API).
- `elements.js`, `render.js`, `llm.js` – rendering helpers, selection logic, and LLM prompt/fallback generation.
- `styles.css` – UI styling.
- `server.py` – FastAPI proxy to keep the OpenAI key off the browser.
- `template.html` – portfolio-level HTML template (used by `generate_report.py`).
- `generate_report.py` – CLI to fill `template.html` via OpenAI; outputs to `dist/report.html`.
- `data.json` – JSON form of the demo data for the CLI/template workflow.

## Quickstart (Static UI)
1) From the repo root: `python -m http.server 8000`
2) Open http://localhost:8000 and use the dropdowns to switch property/hotel/quarter.
   - With `llm_config.enabled` left as `false` (default), the on-page text uses the deterministic fallback narrative.

## Enable LLM Narrative (Browser + Proxy)
1) Python env (example):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn httpx python-dotenv
   ```
2) Create `.env` with `OPENAI_API_KEY=sk-...`
3) Start the proxy: `uvicorn server:app --reload --host 0.0.0.0 --port 8001`
4) Update `data.js` → `llm_config.enabled = true` (and ensure `proxyEndpoint: "/api/qbr-narrative"`).
5) Serve the static files from the same origin as the proxy (e.g., via a reverse proxy) or adjust `proxyEndpoint` to point to the proxy host/port.

## Generate Portfolio HTML via CLI
Uses `data.json` + `template.html` + OpenAI to emit a filled HTML file.
1) Ensure `OPENAI_API_KEY` is set (env or `.env`; `python-dotenv` is supported).
2) Run:
   ```bash
   python generate_report.py \
     --property hilton_regional_portfolio \
     --quarter 2025-Q3 \
     --data data.json \
     --template template.html \
     --output dist/report.html
   ```
3) Open `dist/report.html` in a browser.

## Data Notes
- Structure: `property -> hotels -> quarters -> metrics`. Metrics include financial impact, water/energy/downtime avoided, investment, ROI, payback status, and alert responsiveness.
- `phase2_option` per hotel carries decision deadline, capex, expected savings range, and projected portfolio ROI after phase 2.
- To add real data, mirror the shape in `data.js` (for the interactive UI) and/or `data.json` (for the CLI/template path).

## Troubleshooting
- LLM calls fail/blocked: verify `OPENAI_API_KEY`, proxy is running, and `llm_config.enabled` is true for the target hotel.
- No previous quarter: the UI compares to the immediately prior quarter (sorted by ID); missing data means no ROI snapshot is rendered.
- CORS: keep the proxy and frontend on the same origin or adjust CORS/`proxyEndpoint` accordingly.
