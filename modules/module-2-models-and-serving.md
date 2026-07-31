# Module 2 — Models & Serving: VRAM Math, Bigger Models, and the LAN

| | |
|---|---|
| **Time** | ~2 hours |
| **You start with** | Module 1 complete: `nvidia-smi` works, vLLM installed in `~/vllm-lab/.venv` |
| **You end with** | Two models on disk, an understanding of what fits in VRAM and why, and your server reachable by other machines on the network |
| **Works solo?** | Yes (the partner test in §6 just needs any second machine) |

## What you'll learn

- What a "7B" model actually is, and how to estimate its memory footprint
- Where downloaded models live on disk and how they're cached
- Reading vLLM's startup logs like an operator
- The difference between `localhost` and `0.0.0.0` — serving to the LAN

*New jargon along the way? Every term is defined in the
[Glossary](../appendices/e-glossary.md).*

---

## 0. State check

```bash
cd ~/vllm-lab && source .venv/bin/activate
nvidia-smi                  # GPU visible, ~0 MiB used (no server running)
vllm --version              # prints a version
```

If any of these fail, revisit [Module 1](module-1-install.md).

---

## 1. Concept: parameters, precision, and the VRAM budget

A model like **Qwen2.5-7B-Instruct** has ~7 billion *parameters* — the
learned numbers inside the neural network. Each parameter is stored as a
16-bit number (**FP16/BF16**) = 2 bytes. So:

```
7.6B parameters × 2 bytes  ≈ 15 GB   just to load the weights
```

But weights aren't the whole story. Serving also needs the **KV cache** —
scratch memory holding the attention state of every conversation in flight.
More cache = more simultaneous users and longer conversations.

vLLM's approach: grab a fixed slice of the GPU up front (default **90%**)
and hand everything not used by weights to the KV cache. That's why Module 1's
`nvidia-smi` showed a 3 GB model occupying ~43 GB — the rest is pre-booked
conversation memory, managed by vLLM's signature **PagedAttention** technique
(memory in small pages, like an operating system — the reason vLLM serves
many users efficiently).

Your budget on this hardware (see
[Appendix A](../appendices/a-hardware-profiles.md) for all sites):

| Model | Weights | Fits in 48 GB? |
|---|---|---|
| Qwen2.5-1.5B-Instruct | ~3 GB | Easily, huge KV cache left |
| Qwen2.5-7B-Instruct | ~15 GB | Comfortably — today's workhorse |
| Qwen2.5-32B-Instruct | ~65 GB | ❌ Not at FP16 (quantized or 2-GPU only) |

> 💡 Rule of thumb worth memorizing: **~2 GB per billion parameters at FP16**,
> roughly a quarter of that when 4-bit quantized.

---

## 2. Download the workshop models

vLLM auto-downloads models on first `serve`, but doing it explicitly with the
HuggingFace CLI teaches you where things actually go. The CLI is called `hf`
(older guides say `huggingface-cli` — same tool, older name):

```bash
# The small model — you already have this from Module 1's serve
hf download Qwen/Qwen2.5-1.5B-Instruct

# The workhorse — ~15 GB. Start it and read on while it runs.
hf download Qwen/Qwen2.5-7B-Instruct
```

Both are **ungated** — no account, no license click-through. Famous gated
models like Meta's Llama require a free HuggingFace account and a license
acceptance first; [Appendix B](../appendices/b-gated-models.md) walks that
workflow as homework.

> **🎓 Instructor:** if you pre-cached the 7B per the run-book, this command
> finishes in seconds — a teachable moment in itself: run it, watch it verify
> the cache and exit, then ask the class *why* it was instant. If downloading
> live, stagger the groups; five machines pulling 15 GB at once will crawl.

### Where did 15 GB just go?

```bash
hf cache scan
```

```
REPO ID                     REPO TYPE SIZE ON DISK
--------------------------- --------- ------------
Qwen/Qwen2.5-1.5B-Instruct  model     3.1G
Qwen/Qwen2.5-7B-Instruct    model     15.2G
```

Everything lives under `~/.cache/huggingface/hub/`. Poke around:

```bash
ls ~/.cache/huggingface/hub/
du -sh ~/.cache/huggingface/hub/*
```

The weights are `.safetensors` files — plus a `config.json` (architecture),
`tokenizer.json` (how text becomes tokens), and a chat template. A "model"
is just these files; there's no magic.

**✅ Checkpoint:** `hf cache scan` shows both Qwen models.

---

## 3. Serve the 7B and read the logs like an operator

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct --max-model-len 8192
```

`--max-model-len 8192` caps each conversation at 8,192 tokens (roughly 6,000
words of combined prompt + answer). Shorter max length → less KV cache needed
per conversation → more simultaneous conversations.

This time, *read the startup logs*. Find these lines (order/wording varies by
version):

1. **Weight loading** — how long did 15 GB take from NVMe? (Fast disks matter.)
2. **`GPU KV cache size: N tokens`** — your conversation budget. Divide by
   8,192: that's how many *full-length* conversations could run at once.
3. **`Starting vLLM API server on http://0.0.0.0:8000`** — note `0.0.0.0`, we
   come back to this in §5.
4. **`Application startup complete`** — open for business.

In a second tmux pane, confirm and compare VRAM:

```bash
curl http://localhost:8000/v1/models | jq '.data[].id'
nvidia-smi
```

(`jq` slices fields out of JSON — Module 3 teaches it properly; here it
just prints the model name instead of the whole response blob.)

**✅ Checkpoint:** you can answer: *how many tokens of KV cache did you get,
and how much VRAM is in use?*

> **🎓 Instructor — the VRAM knob (demo):** restart the server with
> `--gpu-memory-utilization 0.5` and compare `nvidia-smi` and the KV cache
> line. Same model, half the memory, smaller cache. This is the knob you'd
> turn to share a GPU between two servers.

### Kensington/Camden only: you have a second GPU

The Precision 5860s have **two** RTX 6000 Adas; vLLM uses GPU 0 by default.
Two options worth knowing (try them if time allows):

```bash
# Run on the second GPU instead (e.g., two servers, one per GPU)
CUDA_VISIBLE_DEVICES=1 vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 8001

# Or: split one big model ACROSS both GPUs (tensor parallelism)
vllm serve Qwen/Qwen2.5-7B-Instruct --tensor-parallel-size 2
```

Tensor parallelism is how the industry serves models too big for any single
GPU — a 70B model on this box would *require* it.

---

## 4. Talk to the bigger model

With the 7B serving, repeat Module 1's chat request — but notice you only
change the `model` field. Same API, different brain:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "Explain what VRAM is to a new intern, in 3 sentences."}]
  }'
```

**Exercise:** ask both models (restart with the 1.5B, or use the second GPU)
the same tricky question — e.g., a two-step word problem. Compare quality.
This is the size/quality trade-off the whole industry lives on.

---

## 5. Concept: `localhost` vs `0.0.0.0` — opening up to the LAN

So far every request came *from the same machine*. The chatbot students build
in Module 4 runs on *other* machines, so your server must accept LAN traffic.

- **`localhost` (127.0.0.1)** — "this machine only." Private loopback.
- **`0.0.0.0`** — "every network interface this machine has," including the
  Ethernet port your LAN sees.

vLLM already binds `0.0.0.0` by default (you saw it in the logs) — so your
server is *already* reachable; you just need to know your address:

```bash
hostname -I        # first address is usually the one, e.g. 10.x.x.x / 192.168.x.x
```

Write your workstation's IP on its label/whiteboard — Module 4 needs it.

> ⚠️ **"Anyone on the network can use my GPU?"** Yes — and today that's a
> feature (your chatbot needs it). On a real deployment you'd add
> `--api-key <secret>` and a firewall. Worth 2 minutes of class discussion:
> what could someone on the LAN do with an open LLM endpoint?

---

## 6. Partner test — the payoff

Pair up with another group. From **their** machine (any machine on the LAN —
a laptop, another workstation):

```bash
curl http://<YOUR_WORKSTATION_IP>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "Which machine are you actually running on?"}]
  }'
```

(Windows laptop? This bash-style command breaks in PowerShell's quoting —
use the PowerShell variant in Module 3 §5, or run the test from another
workstation.)

**✅ Checkpoint:** a machine that is *not* yours gets an answer from *your*
GPU. This client/server split is exactly how the chatbot works in Module 4 —
and how every AI product you've used works.

(The model's answer to "which machine are you on" will be confidently vague
or wrong — a nice first encounter with the fact that models don't know
anything about where they run. They only know text.)

---

## Wrap-up: what you can now do

- [x] Estimate a model's VRAM footprint from its parameter count
- [x] Download models explicitly and inspect the HuggingFace cache
- [x] Read vLLM startup logs: weight load, KV cache size, bind address
- [x] Explain `--max-model-len` and `--gpu-memory-utilization`
- [x] Serve a model to the LAN and hit it from another machine

### Check your understanding

1. Roughly how much VRAM do the *weights* of a 7B model need at FP16 — and
   what's the rule of thumb you used?
2. The model file is 15 GB, but `nvidia-smi` shows ~43 GB in use. Where did
   the rest go, and why does vLLM grab it up front?
3. What does `--max-model-len` limit, and what do you gain by setting it
   *lower*?
4. Your partner's curl to your server hangs. Give two different "arrows"
   that could be broken, and one check for each.

(Answers are in the instructor run-book.)

**Next:** [Module 3 — The CLI Toolkit](module-3-cli-toolkit.md): stop reading
JSON by eye and start scripting the API like a pro.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Download stalls at ~0 B/s | Shared uplink saturated | Stagger groups; `Ctrl-C` and re-run — downloads resume |
| `CUDA out of memory` on serve | Old server still running, or max-model-len too big | `nvidia-smi` → kill stale process; keep `--max-model-len 8192` |
| Partner's curl hangs/refused | Wrong IP, or server bound to localhost | Re-check `hostname -I`; confirm logs say `0.0.0.0`; both machines on same network? |
| `hf: command not found` | venv not activated (hf comes with vLLM's env) | `cd ~/vllm-lab && source .venv/bin/activate` |
| Serve takes minutes "doing nothing" at startup | Normal: weight load + CUDA graph capture | Watch the log lines move; ~1–3 min for 7B is expected |
