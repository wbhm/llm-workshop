# Module 1 — Install & Verify: From Fresh Ubuntu to a Running Model

| | |
|---|---|
| **Time** | ~2 hours |
| **You start with** | A workstation with fresh Ubuntu 24.04, a user account with `sudo`, wired Ethernet |
| **You end with** | NVIDIA driver working, vLLM installed, and a real language model answering requests on your machine |
| **Works solo?** | Yes — instructor sections are marked 🎓 and can be skipped |

## What you'll learn

- How the GPU software stack fits together (driver → CUDA → PyTorch → vLLM)
- Installing and verifying NVIDIA drivers on Ubuntu
- Modern Python environment management with `uv`
- Starting a vLLM server and proving it works

*New jargon along the way? Every term is defined in the
[Glossary](../appendices/e-glossary.md).*

---

## 0. State check — is this machine ready?

Run these before starting. Every command should succeed:

```bash
# You're on Ubuntu 24.04
lsb_release -d          # → "Ubuntu 24.04.x LTS"

# You have sudo rights
sudo true               # → prompts for password, no error

# You have internet over wired Ethernet
ping -c 3 archive.ubuntu.com

# The machine actually has an NVIDIA GPU
lspci | grep -i nvidia  # → at least one line mentioning NVIDIA
```

If `ping` fails but the cable is plugged in, see [Troubleshooting](#troubleshooting)
— Ubuntu 24.04 has known DNS quirks.

> **🎓 Instructor:** demo this state check on the projector machine first.
> This is also your moment to introduce the room layout: which box is whose,
> where the model server will eventually live on the network.

---

## 1. Concept: the stack you're about to build

An LLM answering your question travels through four layers of software.
Installing them **in order, bottom-up** is the whole game today:

```
┌──────────────────────────────────────────────┐
│ 4. vLLM         — serves the model as an API │  ← pip install (10 min)
│ 3. PyTorch/CUDA — math libraries for the GPU │  ← installed *with* vLLM
│ 2. NVIDIA driver — lets Linux talk to GPU    │  ← the risky step (reboot!)
│ 1. Hardware     — RTX 6000 Ada / RTX PRO 5000│  ← already in the box
└──────────────────────────────────────────────┘
```

Most real-world install failures happen at layer 2. That's why we verify each
layer before moving to the next — a habit worth keeping for any sysadmin work.

---

## 2. System prep

Update the package index and install the tools used throughout the workshop:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl jq tmux htop build-essential
```

What these are for:

| Tool | Used in | Purpose |
|------|---------|---------|
| `curl` | Modules 1–4 | Making HTTP requests from the terminal |
| `jq` | Module 3 | Slicing JSON responses |
| `tmux` | Modules 2–4 | Multiple terminal panes: server in one, commands in another |
| `htop` | Any time | Watching CPU/RAM (the CPU-side cousin of Module 3's `nvtop`) |

**✅ Checkpoint:** `jq --version` prints a version number.

---

## 3. Install the NVIDIA driver

Ubuntu ships a tool that detects your GPU and picks the right driver:

```bash
# See what Ubuntu recommends (look for the line ending in "recommended")
ubuntu-drivers devices

# Install the recommended driver
sudo ubuntu-drivers install
```

This takes a few minutes. When it finishes:

```bash
sudo reboot
```

> ⚠️ **Secure Boot must be disabled in BIOS** on these Dell workstations, or
> the NVIDIA kernel module will silently fail to load after reboot. If
> imaging was done per [Appendix C](../appendices/c-ubuntu-imaging.md) this
> is already handled. To check/fix: reboot, press **F12** at the Dell logo →
> BIOS Setup → Boot Configuration → Secure Boot → **Disabled**.
>
> (For the curious: Secure Boot *can* coexist with the driver by enrolling a
> signing key — "MOK enrollment" — but that needs an interactive step at the
> machine's console, so classrooms disable Secure Boot for consistency.)

### Verify layer 2

After the reboot, log back in and run the single most important command of
this workshop:

```bash
nvidia-smi
```

You should see a table listing your GPU(s), driver version, and memory:

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 5xx.xx        Driver Version: 5xx.xx      CUDA Version: 12.x     |
|-------------------------------+----------------------+----------------------|
|   0  NVIDIA RTX 6000 Ada ...            |   ...      |      0%      Default |
|   1  NVIDIA RTX 6000 Ada ...            |   ...      |      0%      Default |
+-----------------------------------------------------------------------------+
```

- **Kensington/Camden:** you'll see **two** RTX 6000 Ada GPUs (48 GB each).
- **Newark:** you'll see **one** RTX PRO 5000 Blackwell (48 GB).

**✅ Checkpoint:** `nvidia-smi` shows your GPU(s) with 0% utilization and a
driver version. If it errors ("command not found" or "couldn't communicate
with the NVIDIA driver"), stop and see [Troubleshooting](#troubleshooting).

> **🎓 Instructor:** pause here and make sure *every* box in the room passes
> `nvidia-smi` before anyone proceeds. Everything else today depends on it,
> and driver problems are much easier to debug in parallel than one-by-one
> later.

---

## 4. Install `uv` and create a Python environment

[`uv`](https://github.com/astral-sh/uv) is a fast, modern Python package
manager. We use it because it automatically picks the PyTorch build that
matches your CUDA version — historically the #1 source of broken LLM installs.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Load it into this shell (new terminals get it automatically)
source ~/.local/bin/env

uv --version
```

Create a project directory and a virtual environment inside it:

```bash
mkdir -p ~/vllm-lab && cd ~/vllm-lab
uv venv --python 3.12 --seed
source .venv/bin/activate
```

Your prompt now shows `(.venv)` — every `pip`/`python` command now uses this
isolated environment instead of the system Python.

> 💡 **Every new terminal** (and every new tmux pane) needs
> `cd ~/vllm-lab && source .venv/bin/activate` before vLLM commands work.
> This will bite you at least once today; now you know why.

**✅ Checkpoint:** `python --version` → 3.12.x, and your prompt shows `(.venv)`.

---

## 5. Install vLLM

```bash
uv pip install vllm --torch-backend=auto
```

This downloads a few gigabytes (PyTorch + CUDA libraries + vLLM) —
expect 5–15 minutes depending on network. While it runs, good discussion:

> **🎓 Instructor discussion while the download runs:** what's actually in
> those gigabytes? (PyTorch, cuBLAS/cuDNN kernels, FlashAttention…) Why does
> `--torch-backend=auto` exist? (PyTorch publishes different wheels per CUDA
> version; picking the wrong one used to be a rite of passage.)

Verify layer 3 and 4:

```bash
# PyTorch can see the GPU (layer 3)
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# → True NVIDIA RTX 6000 Ada Generation   (or RTX PRO 5000 Blackwell)

# vLLM is installed (layer 4)
vllm --version
```

**✅ Checkpoint:** `torch.cuda.is_available()` prints `True`.

---

## 6. Serve your first model

Time to light up the GPU. This command downloads a small model
(Qwen2.5-1.5B-Instruct, ~3 GB) and starts an API server:

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct --max-model-len 4096
```

The first run downloads the model, then you'll see a wall of startup logs.
Learn to spot these landmarks (you'll read them again in Module 2):

```
INFO ... Automatically detected platform cuda.
INFO ... Loading model weights ...
INFO ... GPU KV cache size: ... tokens
INFO ... Starting vLLM API server on http://0.0.0.0:8000
INFO:     Application startup complete.
```

When you see `Application startup complete`, the server is live. **Leave this
terminal running** — the server occupies it (this is why we installed tmux).

### Verify from a second terminal

Open a new terminal (or tmux pane) and ask the server what models it's
serving:

```bash
curl http://localhost:8000/v1/models
```

Then have your first conversation, straight from the command line:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "In one sentence, what does Hopeworks do?"}]
  }'
```

You'll get JSON back with the model's answer buried inside. (Extracting it
cleanly is a Module 3 skill — for now, finding the answer text by eye counts.)

**✅ Checkpoint:** the curl returns JSON containing a `"content"` field with
an actual answer. **You just served your first LLM.**

While the request runs, glance at the GPU in a third terminal:

```bash
nvidia-smi
```

Note the memory usage — the GPU is holding far more than the 3 GB model.
Why is a Module 2 question (spoiler: vLLM pre-books GPU memory for speed).

Stop the server with **Ctrl-C** in its terminal when you're done.

---

## Wrap-up: what you can now do

- [x] Explain the 4-layer GPU software stack
- [x] Install and verify NVIDIA drivers (`nvidia-smi`)
- [x] Create isolated Python environments with `uv`
- [x] Install vLLM and serve a model
- [x] Query an OpenAI-compatible API with curl

### Check your understanding

1. Put the four layers of the stack in order, bottom-up — and for each, name
   the command or step that *verified* it today.
2. `nvidia-smi` fails after the driver install and reboot. What's the first
   thing to check, before touching the driver again?
3. Why did we install vLLM with `uv` and `--torch-backend=auto` instead of
   a plain `pip install`?
4. A new terminal says `vllm: command not found`, but it worked ten minutes
   ago in another window. What happened?

(Answers are in the instructor run-book.)

**Next:** [Module 2 — Models & Serving](module-2-models-and-serving.md), where
you'll download a bigger model, do the VRAM math, and open your server to
the whole network.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `nvidia-smi`: "couldn't communicate with the NVIDIA driver" | Secure Boot blocked the unsigned module | Disable Secure Boot in BIOS (F12 → BIOS Setup), reboot |
| `nvidia-smi`: command not found after install + reboot | Driver install failed partway | `sudo ubuntu-drivers install` again and watch for errors; `sudo apt install nvidia-driver-570` as fallback (Newark Blackwell GPUs need 570+) |
| `ping: Temporary failure in name resolution` | Ubuntu 24.04 systemd-resolved DNS issue (known) | Quick test: `ping -c1 1.1.1.1` — if that works it's DNS. Bypass: `echo "nameserver 1.1.1.1" \| sudo tee /etc/resolv.conf` (temporary; ask instructor before making permanent) |
| `uv: command not found` in a new terminal | PATH not loaded | `source ~/.local/bin/env` or open a fresh login shell |
| `vllm: command not found` | venv not activated | `cd ~/vllm-lab && source .venv/bin/activate` |
| Model download crawls / times out | Shared uplink saturated (everyone downloading at once) | Stagger group downloads; instructor may have pre-cached — retry, it resumes |
| `torch.cuda.is_available()` → `False` | Driver missing or PyTorch got a CPU build | Check `nvidia-smi` first; if OK, reinstall: `uv pip install vllm --torch-backend=auto --reinstall` |
| Server crashes with CUDA out-of-memory | Another vLLM/process already holds the GPU | `nvidia-smi` to find it; one server per GPU |
