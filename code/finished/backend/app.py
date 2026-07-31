"""Hopeworks LLM Workshop -- chatbot backend (finished reference).

A thin FastAPI layer between the browser and a vLLM server.

Run from this directory:
    uvicorn app:app --host 0.0.0.0 --port 8080

Point it at a vLLM server with an environment variable (default: localhost):
    VLLM_BASE_URL=http://192.168.1.50:8000/v1 uvicorn app:app --host 0.0.0.0 --port 8080
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
# The api_key is required by the library but ignored by our server.
client = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key="not-needed")

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
    models = await client.models.list()
    return {"models": [m.id for m in models.data]}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Stream a chat completion back to the browser as Server-Sent Events."""
    messages = list(req.messages)
    if req.system:
        # The system prompt goes first -- it sets the model's persona for
        # the whole conversation.
        messages.insert(0, {"role": "system", "content": req.system})

    async def event_stream():
        try:
            stream = await client.chat.completions.create(
                model=req.model,
                messages=messages,
                stream=True,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    # SSE wire format: "data: <payload>\n\n"
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
        except Exception as exc:  # surface errors in the chat instead of a dead UI
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Serve the beginner frontend from the same server, so opening
# http://<this-machine>:8080/ just works. Mounted last so /api routes win.
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend-html")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
