<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/temp/1

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Agent-driven data fill (Python)

1. Install Python deps (inside `.venv` if desired):
   `pip install openai playwright && playwright install chromium`
2. Put your raw metrics in `services/report_data.json`.
3. Generate the narratives + UI payload:
   `OPENAI_API_KEY=... python services/report_agent.py`
   - Updates `services/report_output.json` (consumed by the React app) and `services/generated_report.html`.
4. Export the filled HTML to PDF:
   `python services/pdf_export.py`
   - Produces `services/generated_report.pdf` with the same front-end design.
