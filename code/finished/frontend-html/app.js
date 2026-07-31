// Hopeworks LLM Workshop -- chatbot frontend (finished reference).
//
// Talks to the FastAPI backend (app.py):
//   GET  /api/models  -> {"models": ["Qwen/Qwen2.5-7B-Instruct", ...]}
//   POST /api/chat    -> Server-Sent Events stream of {"delta": "..."} chunks

// Same origin when the backend serves this page. If you open index.html
// some other way, set this to the backend's address, e.g. "http://192.168.1.50:8080".
const API = "";

const PERSONAS = {
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

// The whole conversation lives HERE, in the browser. The server keeps no
// state -- we re-send the full history with every request (Module 3 lesson).
let messages = [];

// The model we're talking to. A vLLM instance serves exactly one model, so
// we ask the backend which one instead of hardcoding it -- this same app
// then works against ANY server without an edit.
let model = "";

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const formEl = document.getElementById("composer");
const sendBtn = formEl.querySelector("button");
const modelEl = document.getElementById("model");
const personaEl = document.getElementById("persona");
const clearBtn = document.getElementById("clear");

init();

async function init() {
  for (const name of Object.keys(PERSONAS)) {
    personaEl.add(new Option(name, name));
  }
  formEl.addEventListener("submit", onSend);
  clearBtn.addEventListener("click", () => {
    messages = [];
    chatEl.innerHTML = "";
    inputEl.focus();
  });
  await loadModels();
}

async function loadModels() {
  try {
    const res = await fetch(`${API}/api/models`);
    const data = await res.json();
    model = data.models[0];
    modelEl.textContent = model;
  } catch (err) {
    modelEl.textContent = "unavailable";
    addBubble("assistant", `⚠️ Can't reach the backend: ${err.message}`);
  }
}

// Create a chat bubble, append it, scroll it into view. Returns the element
// so the streaming loop can keep updating its text.
function addBubble(role, text) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.textContent = text; // textContent (not innerHTML!) -- model output is untrusted
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
  return el;
}

async function onSend(event) {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text || sendBtn.disabled) return;

  inputEl.value = "";
  sendBtn.disabled = true;

  messages.push({ role: "user", content: text });
  addBubble("user", text);
  const botEl = addBubble("assistant", "…");

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: messages,
        model: model,
        system: PERSONAS[personaEl.value],
      }),
    });

    // Read the SSE stream chunk by chunk and grow the bubble live.
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let answer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by a blank line. The last piece may be
      // incomplete -- keep it in the buffer for the next chunk.
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        if (!evt.startsWith("data: ")) continue;
        const payload = evt.slice("data: ".length);
        if (payload === "[DONE]") continue;

        const data = JSON.parse(payload);
        if (data.error) {
          answer += `\n⚠️ ${data.error}`;
        } else if (data.delta) {
          answer += data.delta;
        }
        botEl.textContent = answer;
        chatEl.scrollTop = chatEl.scrollHeight;
      }
    }

    // Streaming done: the reply becomes part of the history we send next turn.
    messages.push({ role: "assistant", content: answer });
  } catch (err) {
    botEl.textContent = `⚠️ Request failed: ${err.message}`;
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}
