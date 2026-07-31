// API helpers for the Hopeworks chatbot (STARTER -- advanced track).
//
// Your job: complete TODO R1. Requests go to /api/* on the same origin;
// the Vite dev server proxies them to the FastAPI backend (vite.config.js).

export const PERSONAS = {
  "Helpful assistant":
    "You are a helpful, friendly assistant. Keep answers concise.",
  "Hopeworks career coach":
    "You are an encouraging career coach at Hopeworks, a Camden NJ nonprofit " +
    "that trains young adults in tech careers. Give practical, upbeat advice.",
  "Code tutor":
    "You are a patient programming tutor. Explain step by step with small " +
    "examples. Never just hand over a finished answer to homework.",
  "Pirate":
    "You are a pirate. Answer every question accurately, but in pirate speak.",
};

export async function fetchModels() {
  const res = await fetch("/api/models");
  if (!res.ok) throw new Error(`Backend error: ${res.status}`);
  const data = await res.json();
  return data.models;
}

// Async generator: `for await (const delta of streamChat(...))` should yield
// the answer a few characters at a time as the model generates it.
export async function* streamChat({ messages, model, system }) {
  // ── TODO R1 ─────────────────────────────────────────────────────────
  // 1. POST { messages, model, system } to /api/chat (JSON body).
  // 2. Read the SSE stream from res.body.getReader() + TextDecoder:
  //      - accumulate into a buffer
  //      - events are separated by "\n\n"; keep the incomplete tail
  //      - for events starting "data: ": strip the prefix,
  //        skip "[DONE]", JSON.parse the rest
  //      - `throw new Error(data.error)` if the payload has .error
  //      - `yield data.delta` if it has .delta
  //
  // The beginner track's app.js has this same loop inline -- your version
  // just wraps it in a generator so the UI code stays clean.
  // ────────────────────────────────────────────────────────────────────
  yield "TODO R1: implement streamChat";
}
