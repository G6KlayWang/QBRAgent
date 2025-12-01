"""
Render a filled HTML report to PDF using Playwright.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    python services/pdf_export.py
"""

from __future__ import annotations

from pathlib import Path

try:
    from playwright.sync_api import sync_playwright  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("playwright is required. Install with `pip install playwright` and run `playwright install chromium`.") from exc

BASE_DIR = Path(__file__).resolve().parent
HTML_SOURCE = BASE_DIR / "generated_report.html"
PDF_DEST = BASE_DIR / "generated_report.pdf"


def export_html_to_pdf(html_path: Path = HTML_SOURCE, pdf_path: Path = PDF_DEST) -> Path:
    if not html_path.exists():
        raise FileNotFoundError(f"Missing HTML to export: {html_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri())
        page.pdf(path=str(pdf_path), format="Letter", print_background=True)
        browser.close()
    return pdf_path


if __name__ == "__main__":
    destination = export_html_to_pdf()
    print(f"Saved PDF to {destination}")
