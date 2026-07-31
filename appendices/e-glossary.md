# Appendix E — Glossary

Plain-English definitions for every piece of jargon in the workshop,
alphabetical. Linked from each module — when a word doesn't land, look it
up here and go back.

**0.0.0.0** — "listen on every network interface this machine has." A server
bound to 0.0.0.0 is reachable from the LAN. Contrast *localhost*.

**API (Application Programming Interface)** — an agreed format for one
program to ask another for something. In this workshop: HTTP requests with
JSON bodies, sent to the vLLM server.

**Backend** — the server-side part of an app; in Module 4, your FastAPI
program that sits between the browser and vLLM. The **frontend** is the part
that runs in the browser (HTML/JS or React).

**Chat template** — the model-specific text format a conversation is packed
into before the model sees it (who said what, where the system prompt goes).
vLLM applies it for you on the `/v1/chat/completions` endpoint.

**Context length** — the maximum number of tokens (prompt + answer,
whole conversation) a request may use. Set per-server in this workshop with
`--max-model-len`.

**Continuous batching** — vLLM's trick of running many requests through the
GPU *at the same time*, adding and removing them mid-flight. Why one GPU can
serve a whole classroom.

**CORS (Cross-Origin Resource Sharing)** — browser security rules about
which websites may call which servers. The backend enables it so pages
served from one place can call an API served from another.

**CUDA** — NVIDIA's software platform for running general computation
(like neural networks) on their GPUs. PyTorch uses CUDA; vLLM uses PyTorch.

**Driver** — the operating-system software that lets programs talk to a
piece of hardware. `nvidia-smi` working is the proof the GPU driver is
alive.

**Endpoint** — one specific URL an API answers on, e.g. `/v1/models` or
`/v1/chat/completions`.

**FP16 (half precision)** — storing each model parameter as a 16-bit
number (2 bytes). The default for the models in this workshop; the source
of the "~2 GB per billion parameters" rule.

**Gated model** — a model you may download only after accepting a license
with a logged-in account (e.g. Meta's Llama). See Appendix B. Ungated
models (like Qwen) need no account.

**Hallucination** — a model confidently stating something false. Models
predict plausible text; they don't check facts. Treat outputs as drafts.

**HuggingFace** — the site where open models are published and downloaded
from ("GitHub for models"). The `hf` command talks to it.

**Inference** — *running* a trained model to get answers (what this
workshop does), as opposed to *training* one (building it from data).

**KV cache** — GPU memory holding the attention state of conversations in
flight. What vLLM spends most of its pre-booked VRAM on; more KV cache =
more/longer simultaneous conversations.

**LLM (Large Language Model)** — a neural network trained on huge amounts
of text to predict the next token, which turns out to be enough to answer
questions, write code, and chat.

**localhost (127.0.0.1)** — "this machine only." A server bound to
localhost is invisible to the network. Contrast *0.0.0.0*.

**Model weights** — the learned numbers (parameters) that make a model
that model, stored in `.safetensors` files. "Downloading a model" =
downloading its weights plus a few config files.

**OpenAI-compatible API** — the de-facto standard request/response format
for LLM APIs, defined by OpenAI and adopted by vLLM, Ollama, and most
serving tools. Why your chatbot could switch between vLLM and GPT by
changing one URL.

**PagedAttention** — vLLM's signature memory technique: KV-cache memory is
managed in small pages (like an operating system's virtual memory) instead
of big fixed blocks. The reason vLLM wastes so little VRAM per user.

**Parameter** — one learned number inside a model. "7B" = 7 billion
parameters. More parameters ≈ more capable, more VRAM, slower.

**Quantization** — storing weights in fewer bits (e.g. 4-bit instead of
16-bit) to shrink memory use, trading a little quality. Roughly quarters
the "2 GB per billion" rule.

**SSE (Server-Sent Events)** — a simple format for a server to push a
stream of events over one HTTP response: lines of `data: ...` separated by
blank lines. How streamed answers travel in Modules 3 and 4.

**Streaming** — sending the answer a few tokens at a time as they're
generated, instead of all at once at the end. What makes chat UIs feel
alive.

**System prompt** — a hidden instruction placed *first* in the
conversation that steers the model's behavior for every following turn.
The whole mechanism behind Module 4's "personas."

**Temperature** — a sampling knob: near 0 = predictable, focused answers;
higher (0.8–1.5) = varied, creative, riskier. Sent per-request.

**Token** — the unit models actually read and write: a word fragment,
roughly ¾ of an English word on average. Context limits, pricing, and
`max_tokens` all count these.

**venv (virtual environment)** — an isolated per-project Python
installation, so projects' packages don't collide. Created with `uv venv`
(workstations) or `python -m venv` (your machine); activated with
`source .venv/bin/activate`.

**VRAM** — the GPU's own memory, separate from system RAM. The hard limit
on which models fit; the subject of Module 2's arithmetic.
