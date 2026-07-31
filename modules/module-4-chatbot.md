# Module 4 — Build a Web Chatbot on Your Own AI Server

| | |
|---|---|
| **Time** | ~3–4 hours (beginner track); +1–2 h for the React track |
| **You start with** | A vLLM server on the LAN serving Qwen2.5-7B (Modules 1–2), and **your own dev machine meeting the §1 prerequisites** |
| **You end with** | A streaming web chatbot — personas, live model display, ChatGPT-feel — built by you, running on Hopeworks hardware |
| **Works solo?** | Yes |

## What you'll learn

- The three-tier architecture behind every AI product: browser → backend → model server
- Building an API with **FastAPI** and calling an LLM with the **openai** library
- Streaming responses end-to-end with **Server-Sent Events (SSE)**
- Frontend skills: `fetch`, reading a stream, updating the DOM live
- (Advanced track) the same app in **React**, with state and effects

*New jargon along the way? Every term is defined in the
[Glossary](../appendices/e-glossary.md).*

## Tracks

- 🟢 **Beginner track** (§2–§6): FastAPI backend + vanilla HTML/CSS/JS frontend. Do this first even if you know React.
- 🔵 **Advanced track** (§8): rebuild the frontend in React. Same backend.

---

## 0. The architecture — and why a backend at all

```
┌──────────────┐      ┌───────────────────┐      ┌───────────────────┐
│   Browser    │      │   YOUR BACKEND    │      │   vLLM server     │
│  (frontend)  │─────▶│   FastAPI :8080   │─────▶│   :8000           │
│  HTML/JS     │◀─────│   app.py          │◀─────│   Qwen2.5-7B      │
└──────────────┘ SSE  └───────────────────┘ SSE  └───────────────────┘
   your machine           your machine            GPU workstation
                                                     (shared)
```

The browser *could* call vLLM directly — so why build a middle layer? Because
every real AI product has one, for reasons you'll feel today:

1. **Secrets & control** — on a commercial API your key must never reach the
   browser. The backend is where keys, rate limits, and logging live.
2. **Shaping** — the backend injects the persona (system prompt) and decides
   what the frontend is allowed to ask for.
3. **One stable interface** — swap vLLM for OpenAI/Anthropic later and the
   frontend never notices. That's the payoff of the OpenAI-compatible API.

> **🎓 Instructor:** draw this diagram on the board and *leave it up all
> session*. Every bug today is diagnosed by asking "which arrow is broken?"

---

## 1. Prerequisite: your own dev machine, properly configured

**Every student works on their own machine** — no shared keyboards. The
full setup guide (Python, Git + Git Bash, VS Code — all free, ~15 minutes)
is **[Appendix D — Student Machine Setup](../appendices/d-student-machine-setup.md)**;
complete it *before* workshop day.

The one Windows rule worth repeating here: do **all** terminal work in
**Git Bash**, never PowerShell or cmd — this module's commands are written
for bash, and their JSON quoting breaks anywhere else.

Verify you're ready (the last check needs your group's workstation IP from
Module 2):

```bash
python --version      # 3.10 or newer  (macOS: python3 --version)
git --version         # any version
curl http://<WORKSTATION_IP>:8000/v1/models
```

**✅ Checkpoint:** Python ≥ 3.10, git present, VS Code opens, and the curl
returns the model list. If the curl fails while the workstation is up, flag
your instructor — that's a network problem to fix *now*, before any code is
written.

---

## 2. Get the code and run the skeleton

Get the workshop code from your instructor (typically `git clone` of the
workshop repo, or a zip). You'll work in `code/starter/`:

```
starter/
├── backend/           ← §3: your FastAPI app (TODOs 1–3)
│   ├── app.py
│   └── requirements.txt
└── frontend-html/     ← §4: your web UI (TODOs 4–6)
    ├── index.html
    ├── style.css
    └── app.js
```

Install the backend dependencies in a fresh environment and start it:

```bash
cd starter/backend
python -m venv .venv
source .venv/bin/activate        # Windows (Git Bash): source .venv/Scripts/activate

pip install -r requirements.txt

# Tell it where vLLM lives (skip if vLLM is on this same machine).
# Same variable, same form, as Module 3's `ask` script. Works as-is in
# Git Bash on Windows too:
export VLLM_BASE_URL=http://<WORKSTATION_IP>:8000/v1

uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

> 💡 `python -m venv` is Python's built-in environment tool — the
> works-everywhere cousin of the `uv` you used on the workstations. Same
> idea, same result: an isolated `.venv` holding this project's packages.

Open **http://localhost:8080/** in your browser. You'll see the chat UI —
pretty, but hollow: the model name in the header never loads and sending a
message does nothing useful. That's because six TODOs stand between you and
a chatbot.
(`--reload` means the server picks up your edits automatically — save and
retest, no restarts.)

**✅ Checkpoint:** the page loads at `:8080` and the terminal shows uvicorn
running.

---

## 3. Beginner track — the backend (TODOs 1–3)

Open `backend/app.py` in your editor. Read the whole file first — the
scaffolding (imports, request model, CORS, static files) is done; you're
filling in the three pieces that matter.

### TODO 1 — `/api/models`: what's on the menu?

The frontend needs to know which models the vLLM server offers. In Module 3
you did this with curl:

```bash
curl -s http://<ip>:8000/v1/models | jq -r '.data[].id'
```

Now do the same in Python. The `openai` client is already configured
(`client`); inside `list_models()`:

```python
models = await client.models.list()
return {"models": [m.id for m in models.data]}
```

**Test it** (with the vLLM server up):

```bash
curl http://localhost:8080/api/models
# → {"models":["Qwen/Qwen2.5-7B-Instruct"]}
```

Congratulations: your API is now calling another API. That's most of backend
engineering.

### TODO 2 — inject the persona

The frontend sends an optional `system` string (the persona). System prompts
only work as the **first** message, so insert it at the front:

```python
if req.system:
    messages.insert(0, {"role": "system", "content": req.system})
```

That's the whole implementation of "personas" — one message the user never
sees, prepended by the server. Now you know how every "custom GPT" works.

### TODO 3 — stream the answer

The heart of the app. In Module 3 §2 you watched the raw SSE stream with
`curl -N`; now you *produce* one. Inside `event_stream()`, before the
existing `[DONE]` line:

```python
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
            yield f"data: {json.dumps({'delta': delta})}\n\n"
except Exception as exc:
    yield f"data: {json.dumps({'error': str(exc)})}\n\n"
```

Two things worth understanding, not just typing:

- **`yield` makes this a generator** — FastAPI sends each piece to the
  browser the moment it's yielded, instead of waiting for the end. One
  keyword = streaming.
- The **try/except turns failures into chat messages.** Kill the vLLM server
  and your bot says *why* instead of hanging forever. Test this — break it on
  purpose.

**Test the full backend** exactly like you tested vLLM in Module 3:

```bash
curl -sN http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-7B-Instruct", "system": "You are a pirate.", "messages": [{"role": "user", "content": "Hello!"}]}'
```

**✅ Checkpoint:** `data: {"delta": ...}` events stream past, in pirate
speak, ending in `data: [DONE]`. Your backend is finished — everything left
is frontend.

---

## 4. Beginner track — the frontend (TODOs 4–6)

Open `frontend-html/app.js`. Same deal: read it top to bottom first. Notice
`let messages = []` — the Module 3 lesson ("the client carries the history")
made into code.

### TODO 4 — discover the model

A vLLM instance serves exactly **one** model — so there's nothing to "pick,"
but there's something better to do than hardcoding its name: *ask*. In
`loadModels()`:

```javascript
const res = await fetch(`${API}/api/models`);
const data = await res.json();
model = data.models[0];
modelEl.textContent = model;
```

Save, reload the page — the header now shows the model's name, fetched live
from your server. You've closed your first full loop: browser → your
backend → vLLM → back. And because nothing is hardcoded, this exact app
works against *any* server — a fact §5 turns into an experiment.

### TODO 5 — send the conversation

In `onSend()`, the user's message is already in `messages` and on screen;
now POST the whole history plus the UI selections:

```javascript
const res = await fetch(`${API}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: messages,
    model: model,
    system: PERSONAS[personaEl.value],
  }),
});
```

### TODO 6 — read the stream, grow the bubble

The browser-side mirror of TODO 3 (replace the placeholder line):

```javascript
const reader = res.body.getReader();
const decoder = new TextDecoder();
let buffer = "";
let answer = "";

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });

  const events = buffer.split("\n\n");
  buffer = events.pop(); // keep the incomplete tail for the next chunk

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

messages.push({ role: "assistant", content: answer });
```

The subtle line is `buffer = events.pop()`. Network chunks don't respect
event boundaries — a chunk can end mid-`data:` line. Splitting on the blank
line and keeping the unfinished tail is the classic fix; without it you'd get
random `JSON.parse` crashes. (Also note the last line: without it the bot
answers each question but *forgets its own replies* — ask it "what did you
just say?" to prove your fix works.)

**✅ Checkpoint:** save, reload, ask a question — the answer types itself
into the bubble. **You built a streaming AI chatbot.**

---

## 5. Play with what you built

You wrote the mechanism; now feel what it does:

- **Personas** — same question, different personas. Look at `app.py`: the
  only difference is one hidden message.
- **Swap the brain, change nothing** — stop your backend and restart it
  pointed at a *different* server (a neighboring group's IP, or Module 2's
  second-GPU server — note its different port):
  `VLLM_BASE_URL=http://<other-ip>:8000/v1 uvicorn app:app ...`
  (second-GPU server: `http://<same-ip>:8001/v1`).
  Reload the page: the header shows the new model, chat works, and you
  edited zero lines of code. Which model an app talks to is *configuration*,
  not code — that's how real products A/B models and fail over between them.
- **Multi-turn memory** — tell it your name, then ask for it. Then click
  **New chat** and ask again. You know exactly why it forgot: line 1 of
  `messages = []`.
- **Load test** — everyone in class points their backend at ONE workstation
  and chats simultaneously; watch `nvidia-smi` and `/metrics` on that box
  (Module 3 skills). Continuous batching, now with faces.

---

## 6. Challenges (fast finishers)

Ordered by difficulty; each is doable with what you've learned:

1. **Temperature slider** — `<input type="range" min="0" max="1.5" step="0.1">`,
   send its value as `temperature` (the backend already accepts it). Compare
   0.0 vs 1.5 on the same question.
2. **Token counter** — have the backend also yield a final
   `{"usage": ...}` event before `[DONE]` (hint: on the last chunk, vLLM
   includes usage if you pass `stream_options={"include_usage": true}`), and
   display tokens-per-answer in the UI.
3. **Stop button** — abort a generation mid-stream with `AbortController`.
4. **Markdown rendering** — the model emits markdown; render it. Careful:
   you must sanitize (why did `addBubble` use `textContent`?).
5. **Export chat** — download `messages` as a `.json` or `.txt` file.

---

## 7. What you built vs. what the industry runs

Your stack *is* the production pattern, one box smaller:

| Yours | Industry equivalent |
|---|---|
| vLLM on a workstation | vLLM/TGI fleet on GPU cloud |
| FastAPI `app.py` | The product's API service (auth, billing, logging) |
| `messages` array in the browser | Conversation store (database) |
| Persona dropdown | "Custom GPTs" / system-prompt features |
| `VLLM_BASE_URL` env var | Model routing & failover config |

Swap `VLLM_BASE_URL` for `https://api.openai.com/v1` plus a real key and
your app talks to GPT — zero other changes. That is why this workshop taught
the OpenAI-compatible API and not a vendor SDK.

### A note on responsible use

Your chatbot is **lab-grade by design** — know what that means before you
show it off:

- **No authentication.** Anyone on the LAN can use your backend and the GPU
  behind it. Before anything real: `--api-key` on vLLM, plus real auth in
  the backend.
- **Models make things up** — confidently (*hallucination*, see the
  glossary). Treat answers as drafts to verify, never as facts or
  professional advice, and say so to anyone using your bot.
- **Nothing is private.** Prompts flow through a shared workstation and can
  end up in terminal logs. Don't type personal or sensitive information
  into chats on lab machines — yours or anyone else's.
- **The output is your responsibility.** Models reflect their training
  data, biases included. If you ship what a model wrote, *you* shipped it.

### Check your understanding

1. Why must the persona/system message be the *first* message in the list?
2. Name two reasons real products put a backend between the browser and the
   model server instead of calling the model directly.
3. What breaks if you forget `buffer = events.pop()` in the streaming loop —
   and why does it only break *sometimes*?
4. What is the smallest change that would make your finished chatbot talk to
   OpenAI's GPT instead of your vLLM server?

(Answers are in the instructor run-book.)

---

## 8. 🔵 Advanced track — the same app in React

Rebuild the frontend in React with Vite. Same backend, untouched.

**Extra prerequisite:** Node.js 20+ (<https://nodejs.org>) — verify with
`node --version`.

```bash
cd starter/frontend-react
npm install
npm run dev          # → http://localhost:5173
```

Notice `vite.config.js`: the dev server **proxies** `/api` to your backend on
`:8080` — the browser sees one origin, so CORS never comes up. (If your
backend runs on another machine, change the proxy `target`.)

Three TODOs, and note the division of labor — API mechanics live in
`api.js`, UI state lives in `App.jsx`:

- **TODO R1** (`src/api.js`) — implement `streamChat` as an **async
  generator**: the same fetch + reader loop as TODO 5/6, but `yield`ing each
  delta instead of touching the DOM. Compare with your beginner-track code:
  same logic, better shape — the UI can't reach into the network code and
  vice versa.
- **TODO R2** (`src/App.jsx`) — discover the model in a `useEffect` on
  mount: `fetchModels()` resolves to a one-item list (one model per vLLM
  instance) — `setModel(ms[0])`, errors into `setError`.
- **TODO R3** (`src/App.jsx`) — consume your generator:

  ```jsx
  let answer = "";
  for await (const delta of streamChat({ messages: history, model, system: PERSONAS[persona] })) {
    answer += delta;
    setMessages([...history, { role: "assistant", content: answer }]);
  }
  ```

  The React lesson hiding here: we build a **new** array every delta instead
  of mutating, because React re-renders on new references, not changed
  contents. Mutate `messages` directly and the screen freezes while the
  stream flows — try it once on purpose.

**✅ Checkpoint:** the React app streams answers at `:5173` while the vanilla
app still works at `:8080` — two frontends, one backend, which is exactly
the point of having a backend.

**React challenges:** persist the conversation in `localStorage`; extract a
`<Message>` component with a copy button; add the temperature slider as
controlled state.

---

## Troubleshooting

| Symptom | Which arrow is broken? | Fix |
|---|---|---|
| Page loads, model name stuck on "…" or "unavailable" | backend → vLLM | Is vLLM up? Is `VLLM_BASE_URL` right? Test: `curl $VLLM_BASE_URL/models` from the backend machine |
| `curl :8080/api/models` OK but no model name in the browser | browser → backend | Open browser dev tools (F12) → Console/Network for the real error; check TODO 4 |
| Send does nothing, no errors | TODO 5/6 incomplete | Dev tools → Network → click the `/api/chat` request → Response |
| Answer arrives all at once, not streaming | proxy/buffering | Direct uvicorn shouldn't buffer; make sure you `yield` per chunk, not once at the end |
| `JSON.parse` errors mid-answer | split-buffer bug | You must keep the incomplete tail: `buffer = events.pop()` |
| Bot forgets its own last answer | history bug | `messages.push({role:"assistant", ...})` after the stream ends |
| React page: `/api` requests 404 | Vite proxy | Backend not on `:8080`, or proxy `target` wrong in `vite.config.js` |
| Windows: `activate` won't run, or curl says JSON is invalid | You're in PowerShell/cmd, not Git Bash | Open Git Bash ([Appendix D](../appendices/d-student-machine-setup.md)) — there `source .venv/Scripts/activate` and every command in this module works exactly as written |
| Everything works on the workstation but not from your laptop | LAN reachability | `curl http://<ip>:8000/v1/models` from the laptop; same Wi-Fi/VLAN? Ask the instructor about network segmentation |
