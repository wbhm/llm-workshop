# Appendix A — Hardware Profiles by Site

The curriculum is identical at every site; only the numbers below change.
Instructors: skim your site's section before Module 1.

## Kensington / Philadelphia & Camden — Dell Precision 5860 XL

| | |
|---|---|
| Count | Kensington 5, Camden 6 |
| CPU / RAM | Xeon W7-2595X (26C) / 256 GB ECC |
| GPU | **2× NVIDIA RTX 6000 Ada — 48 GB each (96 GB total)** |
| Storage | 2× 2 TB NVMe |
| Shipped OS | Windows 11 Pro (reimage per [Appendix C](c-ubuntu-imaging.md)) |
| CUDA compute capability | 8.9 (Ada) — mature, no special version needs |

**Site notes**

- vLLM uses **GPU 0 only** by default. The second GPU enables the Module 2
  extras: a second server (`CUDA_VISIBLE_DEVICES=1 ... --port 8001`) or
  tensor parallelism (`--tensor-parallel-size 2`).
- With 48 GB per GPU the workshop models fit exactly like Newark's — which
  is why the curriculum needs no changes between sites.
- Stretch demo for instructors: a 32B model (e.g. Qwen2.5-32B-Instruct,
  ~65 GB FP16) *only* runs here, split across both GPUs with `-tp 2`. Great
  "what does more VRAM buy" finale.
- Two NVMe drives → option to keep Windows on disk 0 and put Ubuntu on
  disk 1 (see Appendix C).

## Newark — Dell Pro Max Tower T2

| | |
|---|---|
| Count | 10 |
| CPU / RAM | Core Ultra 9 285K / 64 GB |
| GPU | **NVIDIA RTX PRO 5000 Blackwell — 48 GB** |
| Storage | 2 TB NVMe (single drive — reimaging replaces Windows unless partitioned) |
| Shipped OS | Windows 11 Pro |
| CUDA compute capability | 12.x (Blackwell) — **needs recent driver & vLLM** |

**Site notes**

- **Blackwell is the newest GPU architecture.** Use the newest available
  NVIDIA driver (570+; `sudo ubuntu-drivers install` on Ubuntu 24.04 should
  select it) and the latest stable vLLM. If `vllm serve` fails with errors
  about unsupported compute capability or missing kernels, the fix is
  *upgrade*, not downgrade: `uv pip install -U vllm --torch-backend=auto`.
- Single GPU → skip Module 2's dual-GPU section (it's marked
  "Kensington/Camden only").
- Newark also houses the 72 Pro Micro desktops and 15 laptops — natural
  client machines for Modules 3–4 (integrated graphics is fine; clients
  never run models).

## Camden & Kensington racks — PowerEdge R570 (optional)

| | |
|---|---|
| Count | 1 per site |
| GPU | NVIDIA L4 — 24 GB |

Not a workshop target, but a natural **follow-on project**: after the
workshop, a student team can install vLLM on the R570 the same way (compute
capability 8.9, all Module 1 steps apply) and run Qwen2.5-7B (~15 GB — fits
in 24 GB with reduced `--max-model-len`) as a permanent site-wide endpoint.
The workshop materials are the runbook for exactly that job.

## Model fit matrix (FP16 weights, headroom for KV cache)

| Model | Weights | 48 GB (all sites) | 96 GB / 2 GPU (Kens./Camden) | 24 GB L4 (servers) |
|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | ~3 GB | ✅ | ✅ | ✅ |
| Qwen2.5-7B-Instruct | ~15 GB | ✅ | ✅ | ✅ (tight — cap `--max-model-len`) |
| Llama-3.1-8B-Instruct (Appendix B) | ~16 GB | ✅ | ✅ | ✅ (tight) |
| Qwen2.5-14B-Instruct | ~28 GB | ✅ | ✅ | ❌ |
| Qwen2.5-32B-Instruct | ~65 GB | ❌ | ✅ with `-tp 2` | ❌ |

Rule of thumb from Module 2: **~2 GB per billion parameters at FP16**, plus
KV-cache headroom — aim to keep weights under ~60–70% of VRAM.
