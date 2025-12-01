"""
Minimal FastAPI proxy to keep OpenAI API keys off the browser.

Run locally:
  1) Create a .env with OPENAI_API_KEY=sk-...
  2) uvicorn server:app --reload --host 0.0.0.0 --port 8001

Frontend configuration:
  - In render.js set llm_config.enabled = true and proxyEndpoint = "/api/qbr-narrative".
  - Serve the frontend and proxy under the same origin (e.g., via a small reverse proxy
    or by mounting this app alongside a static server).
"""

import os
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


class NarrativeRequest(BaseModel):
  prompt: str
  model: Optional[str] = "gpt-4o-mini"
  temperature: Optional[float] = 0.4


class NarrativeResponse(BaseModel):
  content: str


@app.post("/api/qbr-narrative", response_model=NarrativeResponse)
async def qbr_narrative(req: NarrativeRequest) -> NarrativeResponse:
  if not OPENAI_API_KEY:
    raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

  payload = {
    "model": req.model,
    "temperature": req.temperature,
    "messages": [
      {
        "role": "system",
        "content": "You write concise QBR narratives. Respond ONLY with JSON matching the requested shape."
      },
      {"role": "user", "content": req.prompt},
    ],
  }

  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}",
  }

  async with httpx.AsyncClient(timeout=30.0) as client:
    resp = await client.post(OPENAI_API_URL, json=payload, headers=headers)

  if resp.status_code != 200:
    raise HTTPException(
      status_code=resp.status_code,
      detail=f"OpenAI error: {resp.status_code} {resp.text}",
    )

  data = resp.json()
  content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
  if not content:
    raise HTTPException(status_code=500, detail="Empty response from OpenAI")

  return NarrativeResponse(content=content)
