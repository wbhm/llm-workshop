# Module 3 — The CLI Toolkit: Interact, Inspect, Monitor

| | |
|---|---|
| **Time** | ~2 hours |
| **You start with** | Modules 1–2 complete; Qwen 1.5B and 7B in the cache |
| **You end with** | Fluency with curl + jq against the API, vLLM's built-in CLIs, cache management, live GPU monitoring — and a CLI tool of your own |
| **Works solo?** | Yes |

## What you'll learn

- Driving an OpenAI-compatible API from the shell: `curl`, `jq`, streaming
- vLLM's built-in client commands: `vllm chat`, `vllm complete`
- Managing the model cache: scan, size, delete
- Monitoring a live server: `nvidia-smi`, `nvtop`, `/health`, `/metrics`

*New jargon along the way? Every term is defined in the
[Glossary](../appendices/e-glossary.md).*

---

## 0. State check + workspace setup

```bash
cd ~/vllm-lab && source .venv/bin/activate
hf cache scan          # both Qwen models present
```

Today runs entirely in **tmux** so the server and your commands share one
screen. Sixty-second tmux course:

```bash
tmux new -s workshop
```

| Keys | Action |
|---|---|
| `Ctrl-b` then `%` | Split pane vertically |
| `Ctrl-b` then `"` | Split pane horizontally |
| `Ctrl-b` then arrow | Move between panes |
| `Ctrl-b` then `d` | Detach (everything keeps running!) |
| `tmux attach -t workshop` | Come back |

Set up three panes: **server** (left), **commands** (top right),
**monitor** (bottom right). In the server pane:

```bash
cd ~/vllm-lab && source .venv/bin/activate
vllm serve Qwen/Qwen2.5-7B-Instruct --max-model-len 8192
```

In the monitor pane:

```bash
watch -n 1 nvidia-smi
```

**✅ Checkpoint:** server says `Application startup complete`; monitor
refreshes every second. All remaining commands go in the commands pane.

---

## 1. curl + jq: reading the API like a pro

In Modules 1–2 you fished answers out of JSON by eye. `jq` does it properly.

### Warm-up on `/v1/models`

```bash
# The raw blob
curl -s http://localhost:8000/v1/models

# Pretty-printed
curl -s http://localhost:8000/v1/models | jq

# Just the model IDs (this exact query reappears in your chatbot's code)
curl -s http://localhost:8000/v1/models | jq -r '.data[].id'
```

(`-s` silences curl's progress bar; `-r` makes jq print raw strings, no
quotes.)

### Extract just the answer from a chat completion

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "Write a haiku about Camden, NJ."}]
  }' | jq -r '.choices[0].message.content'
```

Clean text, no JSON. Deconstruct the jq path: the response has a `choices`
array → take element `[0]` → its `message` → its `content`.

### The other fields matter too

Run it again without the jq filter and find:

- `usage.prompt_tokens` / `usage.completion_tokens` — what you'd be **billed
  for** on a commercial API. Here it's free; the accounting is identical.
- `finish_reason` — `"stop"` means the model chose to end; `"length"` means
  it hit a token cap mid-sentence.

**Exercise:** ask a question and extract *only* the total token count
(`.usage.total_tokens`).

---

## 2. Streaming: why chatbots feel alive

Everything so far waited for the full answer. Real chat UIs show words as
they're generated. Add `"stream": true` and curl's `-N` (no buffering):

```bash
curl -sN http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "stream": true,
    "messages": [{"role": "user", "content": "Count to 10 slowly, one number per line."}]
  }'
```

What scrolls past is **Server-Sent Events (SSE)** — the answer chopped into
`data: {...}` lines, each carrying a few characters in
`choices[0].delta.content`, ending with `data: [DONE]`.

Watch the monitor pane while it streams: GPU utilization jumps while
generating.

> 💡 Remember this wire format. In Module 4 you will *produce* this stream in
> your backend and *consume* it in the browser. Seeing it raw first makes
> that code obvious instead of magical.

---

## 3. vLLM's built-in CLI clients

vLLM bundles interactive clients so you don't need curl for a quick chat:

```bash
# Interactive chat session (Ctrl-D to exit)
vllm chat

# With a system prompt — steer the model's persona
vllm chat --system-prompt "You are a pirate. Answer everything in pirate speak."

# One-shot: ask and exit (great inside scripts)
vllm chat --quick "What is the capital of New Jersey?"

# Raw text completion, no chat formatting (see the difference!)
vllm complete --quick "The three best things about Philadelphia are"
```

**Exercise:** `vllm chat`, ask a question, then ask "what did I just ask
you?" — it remembers, because the client resends the whole conversation each
turn. Then exit, restart, ask again — amnesia. **The server keeps no
conversation state; the *client* carries the history.** This exact fact
shapes your chatbot's design in Module 4.

---

## 4. Cache management: you are now 18 GB heavier

Models pile up fast at 3–15 GB each. Operators need to know:

```bash
# What's on disk and how big?
hf cache scan

# Free space left on the machine?
df -h /

# Delete a model interactively (checkbox UI — DON'T actually delete our
# workshop models; add then remove a tiny test model if you want the rep)
hf cache delete
```

Two environment variables worth knowing (try to answer *why* each exists):

```bash
# Put the cache somewhere else (e.g., a bigger disk)
export HF_HOME=/data/hf-cache

# Never touch the network — fail if a model isn't already local
export HF_HUB_OFFLINE=1
```

**✅ Checkpoint:** you can say how much disk the cache uses and how much
free space remains.

---

## 5. Monitoring a live server

### The GPU: `nvidia-smi` and `nvtop`

Your `watch nvidia-smi` pane shows the essentials: memory used, utilization %,
temperature, and *which processes* hold the GPU. For a nicer live view:

```bash
sudo apt install -y nvtop
nvtop
```

### The server: `/health` and `/metrics`

```bash
# Liveness — 200 means "engine up". This is what load balancers poll.
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health

# Prometheus metrics — the operator's dashboard feed
curl -s http://localhost:8000/metrics | grep -v "^#" | grep vllm | head -20
```

Interesting metrics to grep for: `vllm:num_requests_running`,
`vllm:num_requests_waiting`, `vllm:gpu_cache_usage_perc`,
`vllm:prompt_tokens_total`.

**Load experiment:** fire 5 requests at once, then immediately read metrics:

```bash
for i in 1 2 3 4 5; do
  curl -s http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"Qwen/Qwen2.5-7B-Instruct","messages":[{"role":"user","content":"Tell me a long story."}],"max_tokens":300}' \
    | jq -r '.choices[0].message.content' | head -1 &
done
curl -s http://localhost:8000/metrics | grep vllm:num_requests_running
```

All 5 run *simultaneously* on one GPU — that's vLLM's continuous batching,
the reason it's a production tool and the thing that separates it from
single-user runtimes.

> **🎓 Instructor — the whole-class pile-on:** pick ONE workstation and have
> every student hit it *from their own machine* at the same time, then watch
> that box's `num_requests_running` climb. One GPU, a roomful of users.
>
> The `vllm` command only exists where vLLM is installed (the Linux
> workstations), but the server is just HTTP — any client works. From
> student machines:
>
> ```bash
> # macOS / Linux / Git Bash on Windows
> curl -s http://<TARGET_IP>:8000/v1/chat/completions \
>   -H "Content-Type: application/json" \
>   -d '{"model":"Qwen/Qwen2.5-7B-Instruct","messages":[{"role":"user","content":"Tell me a long story about Camden."}],"max_tokens":300}'
> ```
>
> ```powershell
> # Windows PowerShell (no installs needed)
> Invoke-RestMethod -Uri http://<TARGET_IP>:8000/v1/chat/completions -Method Post -ContentType "application/json" -Body '{"model":"Qwen/Qwen2.5-7B-Instruct","messages":[{"role":"user","content":"Tell me a long story about Camden."}],"max_tokens":300}'
> ```
>
> That "any HTTP client works" fact *is* the lesson — the server doesn't
> know or care what's on the other end. It's also exactly how the Module 4
> chatbot will connect.

---

## 6. Capstone: build `ask` — your own CLI tool

Combine everything into a script. Create `~/bin/ask`:

```bash
mkdir -p ~/bin
nano ~/bin/ask
```

```bash
#!/usr/bin/env bash
# ask — one-shot LLM question from the terminal.
# Usage: ask "why is the sky blue?"
BASE="${VLLM_BASE_URL:-http://localhost:8000/v1}"
MODEL="$(curl -s "$BASE/models" | jq -r '.data[0].id')"

curl -s "$BASE/chat/completions" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg q "$*" --arg m "$MODEL" \
        '{model: $m, messages: [{role: "user", content: $q}]}')" \
  | jq -r '.choices[0].message.content'
```

```bash
chmod +x ~/bin/ask
export PATH="$HOME/bin:$PATH"

ask "give me a one-line shell command to find the 5 biggest files in my home directory"
```

Note the touches that make it a *tool*, not a demo: it auto-discovers the
model from the API, uses `jq -n` to safely build JSON from user input
(quotes in your question won't break it), and honors `VLLM_BASE_URL` so it
can point at any server. Note the URL *includes* the `/v1` suffix — this
exact variable, in this exact form, is how your Module 4 chatbot backend
will find its server too:

```bash
VLLM_BASE_URL=http://<partner-ip>:8000/v1 ask "whose GPU is answering this?"
```

**✅ Checkpoint:** `ask` works against your server *and* a partner's.

---

## Wrap-up: what you can now do

- [x] Query and dissect API responses with curl + jq
- [x] Explain SSE streaming and recognize the wire format
- [x] Use `vllm chat` / `vllm complete`, with system prompts
- [x] Audit and clean the model cache; check disk
- [x] Monitor GPU and server health; explain continuous batching
- [x] Ship a small CLI tool of your own

### Check your understanding

1. Write (from memory) the jq path that extracts just the answer text from
   a chat completion response.
2. In `vllm chat`, the model "remembers" your earlier messages. Where does
   that memory actually live — and what proved it?
3. A response ends with `"finish_reason": "length"`. What happened, and
   what would you change?
4. Five requests fired at once and all ran simultaneously on one GPU. What
   vLLM feature makes that possible?

(Answers are in the instructor run-book.)

**Next:** [Module 4 — Build a Chatbot](module-4-chatbot.md). Everything today
was the command line; now put a real web UI on it.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `jq: parse error` | Response wasn't JSON (server down / HTML error) | Run the curl without jq and read what actually came back |
| `vllm chat` says connection refused | No server running, or wrong URL | Check the server pane; `--url http://localhost:8000/v1` |
| Stream shows nothing for a while | Long prompt processing before first token | Normal for big prompts; watch GPU spike in monitor pane |
| `ask: command not found` | `~/bin` not on PATH in this shell | `export PATH="$HOME/bin:$PATH"` (add to `~/.bashrc` to persist) |
| Metrics grep returns nothing | Server just started, no requests yet | Send one request first, then re-grep |
