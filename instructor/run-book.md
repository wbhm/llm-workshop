# Instructor Run-Book

How to actually deliver this workshop: preparation, timing, room mechanics,
and the failure modes that cost the most minutes.

## The week before

- [ ] Work through all four modules yourself, start to finish, on one real
      workstation. Nothing builds credibility (or catches site-specific
      surprises) like having done it on the actual hardware.
- [ ] Image the workstations — [Appendix C](../appendices/c-ubuntu-imaging.md).
      Verify its final checklist on **every** box.
- [ ] Pre-cache Qwen2.5-7B on each box (Appendix C §5).
- [ ] Confirm the network: student machines and GPU workstations must reach
      each other on ports **8000** (vLLM) and **8080** (backends). Test with
      any two machines and `python3 -m http.server 8000` before assuming.
      Segmented VLANs between "lab" and "student" networks are the classic
      day-of ambush — find out now.
- [ ] **A properly configured per-student machine is a Module 4
      prerequisite** — every student needs their own laptop/desktop with
      Python 3.10+, Git (Git Bash is the required terminal on Windows),
      VS Code, and network reach to the workstations. Verify the machines
      aren't admin-locked against these installs, and send
      [Appendix D](../appendices/d-student-machine-setup.md) (machine
      setup) and the pre-reading to students *ahead of the session* so
      setup happens before workshop day.
- [ ] Get the workshop code where students can fetch it: push this
      `llm-workshop/` folder to a repo they can clone, or stage a zip. Zero-
      infrastructure fallback: on any machine,
      `cd llm-workshop && python3 -m http.server 9000` and have students
      download from `http://<your-ip>:9000`.
- [ ] Print `cheatsheet.md` — one per student.

## Group layout

5 GPU boxes (Kensington) / 6 (Camden) / 10 (Newark) — target **2–3 students
per box**, one box reserved for you (demo + spare when a student box breaks;
"swap to the spare" beats live debugging with an audience). Groups stay with
the same box across all modules — ownership is motivating ("*our* server").

## Session timings

Times assume things go wrong (they will). Each module ends with groups at
the checkpoint state the next module's "state check" expects — **do not**
carry an unfinished install into Module 2; fix or swap boxes.

### Module 1 — Install & Verify (2h)

| Time | What | Mode |
|---|---|---|
| 0:00 | Welcome; the 4-layer stack diagram; state check | Talk + all |
| 0:15 | System prep + driver install on demo box | **I do** |
| 0:30 | Class drives driver install on box 2, discussing each step | **We do** |
| 0:45 | Groups: prep + driver + reboot + `nvidia-smi` on their boxes | **You do** |
| 1:10 | ⛳ *Gate: every box passes `nvidia-smi` before anyone continues* | |
| 1:15 | uv + venv + vLLM install (download runs during discussion) | You do |
| 1:35 | First `vllm serve` + curl; the payoff moment | You do |
| 1:55 | Recap; leave servers stopped | Talk |

Biggest risk: a box failing `nvidia-smi` after reboot. Almost always Secure
Boot (re-enabled or missed) — check `mokutil --sb-state` first, not driver
reinstalls.

### Module 2 — Models & Serving (2h)

| Time | What |
|---|---|
| 0:00 | State check; VRAM-math concept talk (do the 7B arithmetic live on the board) |
| 0:20 | Downloads: 7B command → cache-hit surprise → "why was that instant?" discussion (pre-cache reveal); `hf cache scan` spelunking |
| 0:45 | Serve 7B; groups hunt for the 3 landmark log lines; VRAM-knob demo |
| 1:15 | `hostname -I`, label boxes with IPs, localhost vs 0.0.0.0 talk |
| 1:30 | Partner test across groups; discussion: open GPU on a LAN — feature or bug? |
| 1:50 | Recap |

### Module 3 — CLI Toolkit (2h)

| Time | What |
|---|---|
| 0:00 | State check; tmux 3-pane setup (budget real time — tmux is new to most) |
| 0:20 | curl + jq progression on `/v1/models` then chat |
| 0:45 | Streaming with `curl -N` — have them read the raw SSE out loud |
| 1:00 | `vllm chat` / `complete`; the "server is stateless" experiment |
| 1:15 | Cache management + monitoring; 5-parallel-requests batching demo; **whole-class pile-on**: every student curls ONE box from their own machine at once (curl / PowerShell commands are in Module 3 §5 — no installs needed on student machines), watch metrics climb |
| 1:35 | Capstone: build `ask` |
| 1:55 | Recap |

### Module 4 — Chatbot (3.5–4h, or two half-sessions)

| Time | What |
|---|---|
| 0:00 | Architecture on the whiteboard (leave it up); verify every machine passes the §1 prerequisite checkpoint (setup itself should have happened pre-day) |
| 0:30 | Get code, run skeleton, tour of `app.py` |
| 0:45 | TODO 1 + curl test → TODO 2 → TODO 3 + `curl -N` test |
| 1:45 | *Break — backend done is the natural midpoint (and the split point if running two half-sessions)* |
| 1:55 | Frontend tour; TODO 4 → 5 → 6 |
| 2:55 | Play: personas, model swap, class load-test of one box |
| 3:15 | Challenges / advanced students peel off to React track |
| 3:45 | Demos: each group shows their bot + one thing they customized |

The React track realistically needs its own follow-on session for students
who want it; don't try to run both tracks to completion simultaneously —
point advanced students at §8 and let them self-pace.

### Module 5 — Permanent Server (3h, post-workshop project, 1–2 interns)

Not a cohort session: assign it to a pair who finished Module 4 and want
the resume line. Needs the R570's `hopeworks` password and a site API key
you choose (any long random string; `openssl rand -hex 24`). Confirm with
IT that **8001** is open alongside 8000 before they start.

| Time | What | Mode |
|---|---|---|
| 0:00 | §1–2: process vs service; download both models (start early, read on) | Solo |
| 0:30 | §3: env file + unit + key; reboot test | Solo |
| 1:00 | §4: switch by hand twice | Solo |
| 1:20 | §5: TODOs 1–3 against the running unit | Solo (you review TODO 3 before §6) |
| 2:20 | §6–7: sudoers + manager as a service; final reboot test | Solo |
| 2:50 | Hand-off: they walk you through `guides/intern-dev-setup.md` §5 on a fresh laptop | Review |

Biggest risk: a typo in the sudoers file. The module runs `visudo -c` first
every time; if sudo is already broken, `pkexec visudo` or root console.
Second risk: a stray tmux `vllm serve` holding the GPU when the unit starts
— `nvidia-smi` shows it.

## Failure-mode playbook (cost-ranked)

| Failure | Prevention | In-the-moment fix |
|---|---|---|
| Driver won't load after reboot | Appendix C BIOS checklist | `mokutil --sb-state`; if enabled → BIOS, disable, reboot. Meanwhile group pairs with a neighbor |
| Model download crawls | Pre-cache 7B day before | Stagger; move on to concept material while it pulls |
| Student ↔ workstation traffic blocked | Test cross-VLAN in pre-flight — this is a hard prerequisite with no in-class fallback | Move student machines onto the lab network/switch, or get IT to open ports 8000/8080 between VLANs; Module 4 cannot proceed without it |
| vLLM version breaks on Blackwell (Newark) | Dry-run the week before on a T2 | `uv pip install -U vllm --torch-backend=auto` (newer, never older) |
| Box dies mid-workshop | Keep your demo box as hot spare | Group moves to spare; models are cached there too |
| Student wipes something (venv, cache) | — | Rebuild is Module 1 §4–5, ~15 min; frame it as a rep, not a disaster |
| `Address already in use :8000` | — | A stale server: `pkill -f "vllm serve"` then re-serve |

## Teaching notes

- **Checkpoints are gates, not suggestions.** The modules' ✅ boxes are where
  you walk the room. A group past a broken checkpoint compounds confusion.
- **Let the download minutes work for you** — the modules mark discussion
  prompts precisely where waits happen (vLLM pip install, 7B load).
- **The pirate is load-bearing.** Silly personas are where students discover
  system prompts *matter*; don't skip them for time.
- **Vocabulary payoff:** by the end, students should say "we served a
  7-billion-parameter model with an OpenAI-compatible API and built a
  streaming client against it" — and mean it. Rehearse that sentence in the
  final recap; it's an interview answer.

## Knowledge-check answers

Each module ends with a "Check your understanding" box; use them as exit
tickets or opening recaps. Answers:

### Module 1

1. Hardware (`lspci | grep -i nvidia`) → NVIDIA driver (`nvidia-smi`) →
   PyTorch/CUDA (`torch.cuda.is_available()` → `True`) → vLLM
   (`vllm --version`, then the first serve + curl).
2. Secure Boot — check `mokutil --sb-state` before touching the driver.
   If enabled, the kernel module was blocked from loading.
3. `--torch-backend=auto` makes uv pick the PyTorch build that matches the
   installed CUDA; plain pip can silently grab a mismatched or CPU-only
   build.
4. The new terminal never activated the venv:
   `cd ~/vllm-lab && source .venv/bin/activate`.

### Module 2

1. ~15 GB — the rule of thumb is ~2 GB per billion parameters at FP16.
2. The KV cache. vLLM pre-books a fixed slice of VRAM (default 90%) and
   hands everything not used by weights to conversation memory, so requests
   never wait on allocation.
3. The max tokens per conversation (prompt + answer combined). Lower →
   each conversation reserves less KV cache → more simultaneous
   conversations fit.
4. (a) Network arrow: wrong IP / different network — recheck `hostname -I`
   and curl from a third machine. (b) Server arrow: server died or never
   bound — on the box itself check the logs for
   `Application startup complete` and `curl localhost:8000/v1/models`.

### Module 3

1. `.choices[0].message.content`
2. In the **client** — it re-sends the whole history each turn. Proof: exit
   and restart `vllm chat` and the "memory" is gone, though the server
   never restarted.
3. The answer hit the `max_tokens` cap mid-generation. Raise `max_tokens`
   (or accept truncation).
4. Continuous batching (built on PagedAttention's paged KV-cache memory).

### Module 4

1. The system prompt must precede everything it's supposed to steer; chat
   templates give the first-position system slot special treatment, and a
   "system" message buried mid-conversation is just another message.
2. Any two of: secrets/API keys must never reach the browser; the backend
   enforces control (rate limits, logging, allowed parameters, persona
   injection); it gives the frontend one stable interface so the model
   provider can be swapped invisibly.
3. `JSON.parse` crashes on a half-received SSE event. Network chunk
   boundaries don't respect event boundaries — but they *often happen* to
   align, so the bug is intermittent and timing-dependent (the worst kind).
4. Point `VLLM_BASE_URL` at `https://api.openai.com/v1` and supply a real
   API key. Zero code changes — that's the OpenAI-compatible API paying
   off.

### Module 5

1. A switch is in progress (or the restart failed). Not wrong by itself:
   the env file is *intent*, `/v1/models` is *reality*, and they disagree
   for 1–3 minutes after every switch. `unit: failed` is the signal that
   something *is* wrong.
2. Downloads are slow (minutes to an hour), network-dependent, and eat
   disk; a request that might take an hour is a bad HTTP request. Cost of
   refusing: one manual `hf download` step. Cost of auto-downloading: hung
   requests, surprise disk usage, no way to say no to a 70B.
3. `-n` = non-interactive: fail instead of prompting for a password. It
   succeeds only for the exact commands listed in
   `/etc/sudoers.d/vllm-manager` (`systemctl restart/start/stop vllm`),
   which is why `apt update` is refused.
4. Continue's selected model 404s until the user picks the other entry
   (the model id is in every request). The chatbot's dropdown is stale
   until refreshed (it reads `/api/models` once at load). `/status` tells
   both users what's live and whether the restart has finished.

## After the workshop

Natural follow-ons, in increasing ambition:

1. Challenges from Module 4 §6 as intern project time.
2. React track (§8) for students who did the beginner track.
3. Appendix B (Llama + tokens) as homework.
4. **The real prize:** a student team installs vLLM on the site's PowerEdge
   R570 (L4 GPU) as a *permanent* Hopeworks LLM endpoint — that is
   [Module 5](../modules/module-5-permanent-server.md), and "deployed an
   internal LLM service" is a resume line. Once it's up, every new intern
   onboards against it with the
   [Intern Dev Setup guide](../guides/intern-dev-setup.md).
