# Intern Dev Setup — Your Workstation, the L4 Server, and a Coding Assistant

**Audience:** a new, junior, or intern AI developer at Hopeworks. You will
end up with (1) your own laptop ready for the workshop, (2) vLLM running as
a permanent, key-protected service on the site's **PowerEdge R570** (NVIDIA
L4, 24 GB), (3) two models on disk and a way to switch between them from
any machine, and (4) **VS Code** talking to that server through the
**Continue** coding assistant.

This is a *runbook*: numbered steps, each with a check. The *why* behind
each step lives in the workshop modules it links to — read those when
something is unclear or when a check fails. Nothing here needs a cloud
account, a credit card, or an internet-facing port.

| You need before starting | Ask your instructor for |
|---|---|
| Your own laptop/desktop (Windows, macOS, or Linux), able to install software | — |
| The R570's address on the LAN | `<R570_IP>` |
| The `hopeworks` account password on the R570 (it has `sudo`) | — |
| The **site API key** — one shared secret all clients present to the server | `<SITE_KEY>` |

Everywhere below, `<R570_IP>` and `<SITE_KEY>` mean *your* values. On
Windows, run every command in **Git Bash**, never PowerShell or cmd
([why](../appendices/d-student-machine-setup.md)).

**Time:** ~1 hour if the R570 already has vLLM, ~2 hours from a bare driver.
Sections 1–2 are yours alone; 3–5 touch the shared server (coordinate with
whoever else uses it); 6–7 are back on your laptop.

---

## 1. Your own machine (15 min)

Do [Appendix D](../appendices/d-student-machine-setup.md) in full. In
short: Python 3.10+, Git (Git Bash on Windows), VS Code with the Python
extension, a browser. Then add the one thing Appendix D doesn't cover:

- In VS Code → Extensions sidebar → search **Continue** → install the one
  by *Continue* (publisher `Continue.continue`). A new icon appears in the
  activity bar. Don't configure it yet; that's §6.

**✅ Check:** in Git Bash / Terminal:

```bash
python --version      # ≥ 3.10   (macOS: python3 --version)
git --version
curl --version
```

---

## 2. Verify the server (5 min)

The R570 already has Ubuntu and the NVIDIA driver. Prove it before building
on it:

```bash
ssh hopeworks@<R570_IP>
nvidia-smi
```

You should see **one** GPU named `NVIDIA L4`, memory `24564MiB` total, and
near-zero usage. If `nvidia-smi` errors, stop — the driver is IT's step,
not yours ([Module 1 §3](../modules/module-1-install.md#3-install-the-nvidia-driver)
explains what's wrong).

What 24 GB means for you, using Module 2's rule of thumb (~2 GB per
billion parameters at FP16):

| Model | Weights | On the L4 |
|---|---|---|
| Qwen2.5-1.5B-Instruct | ~3 GB | ✅ easily |
| **Qwen2.5-Coder-7B-Instruct** | ~15 GB | ✅ one at a time, 32k context |
| **Qwen2.5-7B-Instruct** | ~15 GB | ✅ one at a time, 32k context |
| Qwen2.5-14B-Instruct | ~28 GB | ❌ |

One 7B at a time is the constraint the whole "switching" design in §5 exists
to handle.

**✅ Check:** `nvidia-smi` shows `NVIDIA L4`; `lsb_release -d` says Ubuntu
24.04.

---

## 3. Install vLLM on the server (15 min, mostly download)

Still on the R570. This is [Module 1 §2, §4–5](../modules/module-1-install.md)
verbatim; skip any step already done (`vllm --version` works → jump to §4).

```bash
# Tools used throughout
sudo apt update && sudo apt install -y git curl jq tmux htop

# uv: the Python package manager that picks the right PyTorch/CUDA build
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

# An isolated Python 3.12 environment for vLLM
mkdir -p ~/vllm-lab && cd ~/vllm-lab
uv venv --python 3.12 --seed
source .venv/bin/activate

# vLLM + PyTorch + CUDA libraries (a few GB, 5–15 min)
uv pip install vllm --torch-backend=auto
```

**✅ Check:**

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# → True NVIDIA L4
vllm --version
```

> 💡 Every new SSH session needs `cd ~/vllm-lab && source .venv/bin/activate`
> before `vllm`, `hf`, or `python` mean the right thing. The prompt shows
> `(.venv)` when you're in. ([Module 1 §4](../modules/module-1-install.md#4-install-uv-and-create-a-python-environment))

Also fetch the workshop code onto the server — §5 uses its deploy files:

```bash
cd ~ && git clone https://github.com/wbhm/llm-workshop.git
```

---

## 4. Download models (15–40 min, network-bound)

Models come from HuggingFace and land in `~/.cache/huggingface/hub/`.
Download explicitly with the `hf` CLI (it ships with vLLM's environment):

```bash
cd ~/vllm-lab && source .venv/bin/activate

hf download Qwen/Qwen2.5-Coder-7B-Instruct    # coding assistant model, ~15 GB
hf download Qwen/Qwen2.5-7B-Instruct          # workshop chat model, ~15 GB
```

Downloads resume if interrupted; just re-run. Both models are **ungated**
(no account). Gated ones like Llama need a token first —
[Appendix B](../appendices/b-gated-models.md).

**To download any other model**, the pattern is the same: find its id on
<https://huggingface.co> (the `org/name` in the URL), check it fits
(parameters × 2 GB < ~17 GB on this card), then `hf download <org/name>`.
vLLM will also auto-download on first serve, but explicit is easier to
monitor.

**✅ Check:**

```bash
hf cache scan          # both Qwen repos, ~15 GB each
df -h /                # still ≥ 40 GB free
```

([Module 2 §2](../modules/module-2-models-and-serving.md#2-download-the-workshop-models)
explains what's inside those folders; [Module 3 §4](../modules/module-3-cli-toolkit.md#4-cache-management-you-are-now-18-gb-heavier)
covers cleaning up.)

---

## 5. Run vLLM as a service, and switch models over the API (30 min)

This is the deploy half of [Module 5](../modules/module-5-permanent-server.md).
Module 5 has you *build* the switcher as an exercise; this section just
*installs* the finished one. Do the module later if you want to understand
the code — you will be its maintainer.

### 5a. Install the service (on the R570)

```bash
cd ~/llm-workshop/code/finished/model-manager

# 1. Configuration: the model, the context length, the site key
sudo mkdir -p /etc/vllm
sudo cp deploy/vllm.env.example /etc/vllm/vllm.env
sudo chown hopeworks:hopeworks /etc/vllm /etc/vllm/vllm.env
sudo chmod 640 /etc/vllm/vllm.env
nano /etc/vllm/vllm.env          # VLLM_API_KEY=<SITE_KEY>   (no quotes)

# 2. vLLM as a boot-time service
sudo cp deploy/vllm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vllm
journalctl -u vllm -f            # wait for "Application startup complete", then Ctrl-C

# 3. The switcher: one precise sudo right, then its own service
sudo visudo -c -f deploy/sudoers-vllm-manager
sudo install -m 0440 deploy/sudoers-vllm-manager /etc/sudoers.d/vllm-manager
mkdir -p ~/model-manager && cp manager.py ~/model-manager/
sudo cp deploy/model-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now model-manager
```

The server now exposes two things, both requiring
`Authorization: Bearer <SITE_KEY>`:

| Port | What | Endpoints you'll use |
|---|---|---|
| **8000** | vLLM, OpenAI-compatible | `GET /v1/models`, `POST /v1/chat/completions`, `GET /health` (no key) |
| **8001** | model manager | `GET /models` (on disk), `GET /status` (what's live), `POST /switch` |

**✅ Check (on the R570):**

```bash
curl -s http://localhost:8000/v1/models | jq                       # 401 — the key works
curl -s http://localhost:8000/v1/models -H "Authorization: Bearer <SITE_KEY>" | jq -r '.data[].id'
curl -s http://localhost:8001/status  -H "Authorization: Bearer <SITE_KEY>" | jq
```

Expect `Qwen/Qwen2.5-Coder-7B-Instruct` from the first, and `"ready": true`
from the second.

### 5b. Switch models — from your laptop

Set two variables once per terminal session:

```bash
export MGR=http://<R570_IP>:8001
export AUTH="Authorization: Bearer <SITE_KEY>"
```

**What's on disk** (what you *can* switch to):

```bash
curl -s $MGR/models -H "$AUTH" | jq
```

**What's live right now:**

```bash
curl -s $MGR/status -H "$AUTH" | jq
```

**Switch** (takes 1–3 minutes; `"wait": true` makes the request block until
the new model answers):

```bash
curl -s -X POST $MGR/switch -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-7B-Instruct", "wait": true}'
```

Switch back to the coder the same way. Asking for a model that isn't on
disk returns a `400` telling you to `hf download` it (§4) — the manager
never downloads on its own.

**Why is there no `POST /v1/load_model` in vLLM itself?** One vLLM process
serves one model; loading 15 GB of weights holds the whole GPU for minutes.
The manager does what an operator would do by hand: rewrite the config,
restart the service, wait for health. [Module 5 §4](../modules/module-5-permanent-server.md#4-switching-by-hand-so-you-know-what-youre-automating)
has you do it by hand first.

**✅ Check:** after a switch, `curl -s http://<R570_IP>:8000/v1/models -H "$AUTH" | jq -r '.data[].id'`
prints the model you asked for.

> ⚠️ **It's a shared GPU.** A switch kicks every current user off the old
> model for a couple of minutes. Say so in the team chat before you do it.

---

## 6. Connect VS Code (Continue) to the server (10 min)

Continue is an open-source VS Code assistant that talks to any
OpenAI-compatible server. One YAML file points it at the R570.

1. In VS Code, click the Continue icon in the activity bar. In the chat
   panel, open the **gear / settings** and choose to edit the **local
   config** — this opens `~/.continue/config.yaml`
   (Windows: `%USERPROFILE%\.continue\config.yaml`). Any editor works too.
2. Replace its contents with [`continue-config.yaml`](continue-config.yaml)
   from this folder, filling in `<R570_IP>` and `<SITE_KEY>`. Keep the
   `/v1` suffix on the URL — it's the same `VLLM_BASE_URL` form the
   workshop uses everywhere.
3. Save. Continue reloads automatically. In the chat panel's model
   dropdown you'll see both Hopeworks entries; pick **whichever is live**
   (§5b `/status`). The other errors until you switch the server.

What the config does, line by line:

| Key | Meaning |
|---|---|
| `provider: openai` | "speak the OpenAI API" — vLLM does |
| `model:` | must equal an id from `/v1/models`, exactly |
| `apiBase:` | the server, with `/v1` |
| `apiKey:` | the site key, sent as `Authorization: Bearer` |
| `roles: chat, edit, apply` | use this model for chat, inline edits (Ctrl/Cmd-I), and applying diffs |
| `capabilities: tool_use` | enables **Agent** mode; works because the server runs `--tool-call-parser hermes` |
| `contextLength: 32768` | must not exceed the server's `MAX_MODEL_LEN` |

**✅ Check — three features, in order:**

1. **Chat:** open any `.py` file, select a function, press Ctrl/Cmd-L
   (adds it to chat), ask *"explain this function"*. A streamed answer
   means the whole chain works.
2. **Edit:** select a few lines, Ctrl/Cmd-I, type *"add a docstring"*,
   accept the diff.
3. **Agent:** switch the mode selector to Agent, ask *"list the files in
   this project and summarize what the app does"*. The model calls a tool
   to read the tree.

**What to expect from a 7B model:** fast, good at explaining and small
edits, unreliable on long multi-step agent tasks — it may loop or
hallucinate a file. That's the model, not your setup. Keep agent tasks
small and specific. If chat works but agent mode doesn't, confirm the live
model is the **Coder** one and that the unit file has the two tool-calling
flags.

Continue ships no autocomplete model in this config on purpose: ghost-text
autocomplete wants a dedicated small FIM model and a second server, which
the L4 can't spare alongside a 7B. It's a documented stretch goal in
Continue's own docs if you want it later.

---

## 7. Point the workshop chatbot at the server (5 min)

The Module 4 backend reads two environment variables, so no code changes:

```bash
cd llm-workshop/code/finished/backend
source .venv/bin/activate                      # Windows: source .venv/Scripts/activate
VLLM_BASE_URL=http://<R570_IP>:8000/v1 VLLM_API_KEY=<SITE_KEY> \
  uvicorn app:app --host 0.0.0.0 --port 8080
```

Open <http://localhost:8080/>. The model dropdown shows whatever is live on
the R570 — switch the server (§5b), refresh the page, and the dropdown
follows.

---

## Daily use

```bash
# start of every laptop terminal session
export MGR=http://<R570_IP>:8001
export AUTH="Authorization: Bearer <SITE_KEY>"
curl -s $MGR/status -H "$AUTH" | jq          # what's live?
```

| Symptom | Check first | Then |
|---|---|---|
| Continue: "401" / "Unauthorized" | `apiKey` in config = key in `/etc/vllm/vllm.env`? | No quotes around the key in the env file |
| Continue: "model not found" / 404 | Model dropdown = live model? (`/status`) | Switch server or pick the other entry |
| Continue: connection refused / timeout | `curl http://<R570_IP>:8000/health` from laptop | Server restarting (1–3 min)? Firewall on 8000/8001? Same LAN? |
| `/switch` → 500 "password is required" | sudoers rule installed (§5a step 3)? | `sudo visudo -c -f deploy/sudoers-vllm-manager` then reinstall |
| `/switch` → 400 "not in the cache" | `hf cache scan` on the R570 *as hopeworks* | `hf download <id>` first |
| Server: CUDA out of memory | `nvidia-smi` on the R570 — a stray `vllm serve` in tmux? | `pkill -f "vllm serve"; sudo systemctl restart vllm` |
| Everything slow | `curl -s :8000/metrics \| grep num_requests_running` | Someone's hammering it; it's one GPU |

Server-side commands you own ([Module 5 §3b](../modules/module-5-permanent-server.md#3b-the-unit-file)):

```bash
systemctl status vllm model-manager
journalctl -u vllm -n 100
sudo systemctl restart vllm
```

Full command list: [cheatsheet.md](../cheatsheet.md). Jargon:
[Glossary](../appendices/e-glossary.md).
