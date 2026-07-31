# Hopeworks LLM Workshop — Serving Open Models with vLLM

A four-module, hands-on workshop that takes Hopeworks interns from a fresh
Ubuntu workstation to a working, web-based AI chatbot powered by a local
[vLLM](https://docs.vllm.ai) server.

**No cloud accounts, no API bills, no gated downloads required** — everything
runs on Hopeworks' own GPU workstations, on the local network.

## What students build

By the end of the workshop, each student group will have:

1. A GPU workstation running Ubuntu 24.04 with NVIDIA drivers and vLLM installed **(Module 1)**
2. Two open-source models (Qwen2.5 1.5B and 7B) downloaded and served over an OpenAI-compatible API **(Module 2)**
3. Command-line fluency: querying, scripting, and monitoring the model server **(Module 3)**
4. A streaming web chatbot — with personas and live model discovery — talking to their server **(Module 4)**

## Who this is for

Hopeworks interns with:

- **Basic terminal comfort** — you can open a terminal and run commands like
  `cd` and `ls`. Every command beyond that is taught as it's used.
- **Some HTML/JavaScript exposure** — helpful for Module 4's beginner track
  (the Hopeworks web-dev curriculum is plenty). The React track additionally
  assumes React basics.
- **No Linux, Python, or AI experience required.**

**Pre-reading (~30 min):** [Ollama vs vLLM](pre-reading-ollama-vs-vllm.md) —
what these tools are, how they differ, and why this workshop uses vLLM.
Jargon that trips you up anywhere in the workshop is defined in the
[Glossary](appendices/e-glossary.md).

## Architecture at a glance

```
┌──────────────────┐        ┌─────────────────────┐        ┌──────────────────┐
│  Student laptop  │  HTTP  │  FastAPI backend     │  HTTP  │  GPU workstation │
│  (browser)       │───────▶│  (port 8080)         │───────▶│  vLLM server     │
│                  │◀───────│  streams SSE         │◀───────│  (port 8000)     │
└──────────────────┘        └─────────────────────┘        └──────────────────┘
     Module 4                     Module 4                    Modules 1–3
```

The key idea threaded through every module: **vLLM speaks the same API as
OpenAI**. Every skill learned here — curl calls, streaming, system prompts,
the `openai` client library — transfers directly to commercial AI APIs
students will meet on the job.

## The modules

| # | Module | Time | Students do |
|---|--------|------|-------------|
| 1 | [Install & Verify](modules/module-1-install.md) | ~2 h | NVIDIA driver → `uv` → vLLM → first model served |
| 2 | [Models & Serving](modules/module-2-models-and-serving.md) | ~2 h | Download models, VRAM math, serve to the LAN |
| 3 | [The CLI Toolkit](modules/module-3-cli-toolkit.md) | ~2 h | curl + jq, `vllm chat`, cache management, monitoring |
| 4 | [Build a Chatbot](modules/module-4-chatbot.md) | ~3–4 h | FastAPI backend + web frontend, streaming chat |

Each module is **standalone and self-paced**: it opens with a prerequisites
"state check" so a student can verify their machine is ready, and can be run
instructor-led or solo. Instructor-only notes appear in blocks marked
**🎓 Instructor**.

## Repository layout

```
llm-workshop/
├── README.md                  ← you are here
├── pre-reading-ollama-vs-vllm.md ← 30-min background read (assign before Module 1)
├── cheatsheet.md              ← 1-page command reference (print this)
├── modules/                   ← the four student-facing tutorials
├── code/
│   ├── starter/               ← skeletons with TODOs (students work here)
│   └── finished/              ← complete reference implementations
├── appendices/
│   ├── a-hardware-profiles.md ← per-site GPU specifics (Kensington/Camden/Newark)
│   ├── b-gated-models.md      ← stretch goal: HuggingFace tokens & Llama
│   ├── c-ubuntu-imaging.md    ← pre-flight: getting Ubuntu onto the workstations
│   ├── d-student-machine-setup.md ← dev-env prerequisites for every student (send ahead!)
│   └── e-glossary.md          ← plain-English definitions of all workshop jargon
└── instructor/
    └── run-book.md            ← timing, pre-flight checklist, failure modes, quiz answers
```

## Teaching model

Every hands-on section follows **"I do → we do → you do"**:

1. **I do** — instructor demos the step on the projector.
2. **We do** — the class configures *one* workstation together, instructor driving questions.
3. **You do** — student groups repeat it on their own workstation using the written module.

## Hardware requirements

The workshop targets Hopeworks' GPU workstations (see
[Appendix A](appendices/a-hardware-profiles.md) for per-site details):

| Site | GPU hosts | GPU | VRAM |
|------|-----------|-----|------|
| Kensington | 5× Dell Precision 5860 | 2× RTX 6000 Ada | 96 GB (2×48) |
| Camden | 6× Dell Precision 5860 | 2× RTX 6000 Ada | 96 GB (2×48) |
| Newark | 10× Dell Pro Max T2 | RTX PRO 5000 Blackwell | 48 GB |

All model choices in this curriculum fit within **48 GB** — the smallest
target GPU — so the same materials work at every site unchanged.

**Per-student dev machines are a Module 4 prerequisite:** each student needs
their own laptop/desktop with a browser, Python 3.10+, Git (Git Bash on
Windows), and VS Code — setup steps are in
[Appendix D](appendices/d-student-machine-setup.md) and take ~15 minutes.
No GPU needed on student machines.

## Before workshop day

Instructors: work through the [run-book](instructor/run-book.md) and
[Appendix C](appendices/c-ubuntu-imaging.md) at least one day ahead —
imaging machines and pre-caching the 7B model the afternoon before saves
about 45 minutes of class time per session. Send students
[Appendix D (machine setup)](appendices/d-student-machine-setup.md) and the
[pre-reading](pre-reading-ollama-vs-vllm.md) ahead of the session.
