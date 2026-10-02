"""Hopeworks LLM Workshop -- chatbot backend (STARTER).

Your job: complete TODO 1, 2 and 3. Module 4 walks through each one.

Run from this directory:
    uvicorn app:app --host 0.0.0.0 --port 8080 --reload

Point it at a vLLM server with an environment variable (default: localhost):
    VLLM_BASE_URL=http://192.168.1.50:8000/v1 uvicorn app:app --host 0.0.0.0 --port 8080 --reload
"""

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from pydantic import BaseModel

VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")

# vLLM speaks the OpenAI API, so we use the official OpenAI client library.
# Workshop workstations ignore the key; a server started with --api-key
# (the R570 in Module 5) requires it. Default keeps the workshop unchanged.
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "not-needed")
client = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key=VLLM_API_KEY)

app = FastAPI(title="Hopeworks Chatbot")

# Allow browsers on other origins (e.g. the React dev server on :5173)
# to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """What the frontend sends us for each message."""

    messages: list[dict]  # the whole conversation: [{"role": ..., "content": ...}]
    model: str
    system: str | None = None  # persona / system prompt
    temperature: float = 0.7
    max_tokens: int = 1024


@app.get("/api/models")
async def list_models():
    """Ask the vLLM server which models it is serving."""
    # ── TODO 1 ──────────────────────────────────────────────────────────
    # Ask vLLM for its model list and return it as {"models": [...ids...]}.
    #
    # Hints:
    #   - `await client.models.list()` returns an object with a `.data` list
    #   - each item in `.data` has an `.id` (the model name)
    #   - you did the curl version of this in Module 3:
    #       curl :8000/v1/models | jq -r '.data[].id'
    # ────────────────────────────────────────────────────────────────────
    return {"models": []}  # replace me


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Stream a chat completion back to the browser as Server-Sent Events."""
    messages = list(req.messages)

    # ── TODO 2 ──────────────────────────────────────────────────────────
    # If the request includes a persona (req.system), insert it as a
    # {"role": "system", "content": ...} message at the FRONT of `messages`.
    # The system prompt must come first to steer the whole conversation.
    # ────────────────────────────────────────────────────────────────────

    async def event_stream():
        # ── TODO 3 ──────────────────────────────────────────────────────
        # Call vLLM with streaming on, and forward each chunk to the
        # browser in SSE format. Steps:
        #
        #   1. stream = await client.chat.completions.create(
        #          model=req.model, messages=messages, stream=True,
        #          temperature=req.temperature, max_tokens=req.max_tokens)
        #   2. async for chunk in stream:
        #          the new characters are chunk.choices[0].delta.content
        #          (it can be None -- skip those)
        #   3. for each piece of text, yield an SSE event:
        #          yield f"data: {json.dumps({'delta': text})}\n\n"
        #
        # You watched this exact wire format scroll past in Module 3 §2.
        # Wrap it in try/except and yield {'error': str(exc)} on failure,
        # so a dead vLLM server shows up in the chat instead of hanging.
        # ────────────────────────────────────────────────────────────────
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Serve the beginner frontend from the same server, so opening
# http://<this-machine>:8080/ just works. Mounted last so /api routes win.
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend-html")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
