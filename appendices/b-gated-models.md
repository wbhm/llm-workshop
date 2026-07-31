# Appendix B — Stretch Goal: Gated Models (Llama) and HuggingFace Tokens

Everything in the core workshop used **ungated** models — anyone can
download them, no account needed. But many famous models (Meta's **Llama**,
Google's **Gemma**) are **gated**: free, but you must accept a license with a
HuggingFace account first. Knowing this workflow matters on the job, and
it's a nice thing to have on your resume next to "Llama."

This is homework/self-paced material — it involves a wait (license approval)
that doesn't fit class time.

## 1. Create a HuggingFace account

<https://huggingface.co/join> — free. HuggingFace is "GitHub for models":
the place virtually all open models are published.

## 2. Request access to Llama

Visit <https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct>, log in, and
you'll see a license gate instead of a download. Fill in the form and accept
Meta's community license.

Approval is usually minutes-to-hours, occasionally longer. You'll get an
email; the model page will show "You have been granted access."

## 3. Create an access token

A token is how the command line proves it's you (downloads of gated models
are authorized per-account):

1. HuggingFace → Settings → **Access Tokens** → Create new token.
2. Type: **Read** is enough.
3. Copy it immediately — it's shown once. Treat it like a password: never
   commit it to git, never paste it in shared docs.

## 4. Log in on the workstation

```bash
cd ~/vllm-lab && source .venv/bin/activate
hf auth login          # paste the token when prompted
hf auth whoami         # verify
```

The token is stored under `~/.cache/huggingface/` — you only do this once
per machine (and per user account; remember this box is shared).

## 5. Download and serve — everything else is identical

```bash
hf download meta-llama/Llama-3.1-8B-Instruct     # ~16 GB

vllm serve meta-llama/Llama-3.1-8B-Instruct --max-model-len 8192
```

Every Module 2–4 skill now applies verbatim — including your chatbot: point
it at this server and the header simply shows the new model (that's TODO 4
paying off). Ask Llama and Qwen the same
questions and compare; they're both ~8B, trained by different labs on
different data.

## Common errors

| Error | Meaning | Fix |
|---|---|---|
| `401 Unauthorized` / `Access to model ... is restricted` | Not logged in, or access not granted yet | `hf auth whoami`; check the model page for "granted access"; wait for the approval email |
| `You need to agree to share your contact information` | License gate never accepted | Do step 2 in the browser while logged in |
| Token works for you, fails for your teammate | Access is per-account | Each person requests access with their own account |
