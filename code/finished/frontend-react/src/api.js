// API helpers for the Hopeworks chatbot.
//
// Requests go to /api/* on the same origin; the Vite dev server proxies
// them to the FastAPI backend (see vite.config.js).

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

// Async generator: `for await (const delta of streamChat(...))` yields the
// answer a few characters at a time as the model generates it.
export async function* streamChat({ messages, model, system }) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, model, system }),
  });
  if (!res.ok) throw new Error(`Backend error: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE events are separated by a blank line; keep any incomplete
    // trailing piece in the buffer for the next chunk.
    const events = buffer.split("\n\n");
    buffer = events.pop();

    for (const evt of events) {
      if (!evt.startsWith("data: ")) continue;
      const payload = evt.slice("data: ".length);
      if (payload === "[DONE]") continue;

      const data = JSON.parse(payload);
      if (data.error) throw new Error(data.error);
      if (data.delta) yield data.delta;
    }
  }
}
