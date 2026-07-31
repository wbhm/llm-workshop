import { useEffect, useRef, useState } from "react";
import { fetchModels, streamChat, PERSONAS } from "./api.js";
import "./App.css";

export default function App() {
  // A vLLM instance serves exactly one model -- we ask the backend which
  // one instead of hardcoding it, so this app works against any server.
  const [model, setModel] = useState("");
  const [persona, setPersona] = useState(Object.keys(PERSONAS)[0]);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    // ── TODO R2 ───────────────────────────────────────────────────────
    // On mount: fetchModels() resolves to a list with ONE id (a vLLM
    // instance serves one model) -- setModel(ms[0]). Catch errors into
    // setError(...).
    // ──────────────────────────────────────────────────────────────────
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;

    setDraft("");
    setError("");
    setBusy(true);

    // History is client-side state; the server is stateless (Module 3).
    const history = [...messages, { role: "user", content: text }];
    setMessages([...history, { role: "assistant", content: "" }]);

    try {
      // ── TODO R3 ─────────────────────────────────────────────────────
      // Stream the reply and re-render as it grows:
      //
      //   let answer = "";
      //   for await (const delta of streamChat({
      //     messages: history,
      //     model,
      //     system: PERSONAS[persona],
      //   })) {
      //     answer += delta;
      //     setMessages([...history, { role: "assistant", content: answer }]);
      //   }
      //
      // Why `[...history, {...}]` instead of mutating? React only
      // re-renders when it sees a NEW array/object -- immutability is
      // what makes the bubble grow on screen.
      // ────────────────────────────────────────────────────────────────
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Hopeworks Chatbot</h1>
        <div className="controls">
          <div className="model-info">
            Model
            <span>{model || "…"}</span>
          </div>
          <label>
            Persona
            <select value={persona} onChange={(e) => setPersona(e.target.value)}>
              {Object.keys(PERSONAS).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={() => setMessages([])}>
            New chat
          </button>
        </div>
      </header>

      <main className="chat">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.content || "…"}
          </div>
        ))}
        {error && <div className="error">⚠️ {error}</div>}
        <div ref={bottomRef} />
      </main>

      <form className="composer" onSubmit={handleSend}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask me anything…"
          autoFocus
        />
        <button type="submit" disabled={busy}>
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
