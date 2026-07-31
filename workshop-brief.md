# Workshop Brief: Serving AI Models on Hopeworks Hardware

**A hands-on technical workshop for Hopeworks interns — from bare workstation
to a working AI chatbot, built entirely on equipment Hopeworks already owns.**

*Prepared for Hopeworks staff and leadership. All curriculum materials are
complete and published at <https://github.com/wbhm/llm-workshop>.*

---

## What it is

A four-module, instructor-led workshop (~10 contact hours) in which interns
stand up a real AI serving stack from scratch and then build a web
application on top of it:

| Module | Session | Students... |
|---|---|---|
| 1. Install & Verify | ~2 h | Install NVIDIA drivers and the vLLM AI server on a fresh Ubuntu workstation |
| 2. Models & Serving | ~2 h | Download open-source AI models, learn GPU memory sizing, serve models over the office network |
| 3. The CLI Toolkit | ~2 h | Query, script, and monitor the model server from the command line |
| 4. Build a Chatbot | ~3.5–4 h | Each student builds their own streaming web chatbot (ChatGPT-style) against the class's model servers |

Teaching follows an *"I do → we do → you do"* model — instructor demo, one
guided group build, then student groups replicate independently — and every
module doubles as a self-paced tutorial for students who miss a session or
want to go again.

## Why this matters for Hopeworks

- **Directly employable skills.** Linux administration, GPU infrastructure,
  APIs, Python, and web development — assembled into one coherent, working
  system students can explain end-to-end. By design, each student leaves able
  to say in an interview: *"I served a 7-billion-parameter AI model with an
  OpenAI-compatible API and built a streaming web client against it."*
- **AI skills without AI gatekeeping.** The workshop uses the same API
  standard as OpenAI and Anthropic, so everything learned transfers directly
  to commercial AI work — but requires no cloud accounts, no API bills, and
  no vendor sign-ups for students.
- **It uses what Hopeworks already bought.** The GPU workstations at each
  site are the entire infrastructure. Software is 100% free and open source.
- **It builds toward something permanent** (see "After the workshop" below).

## Who and where

- **Audience:** Hopeworks interns. Assumed background is deliberately
  modest — basic terminal comfort and some HTML/JavaScript exposure (in line
  with Hopeworks' web-dev training); no Linux, Python, or AI experience
  required. An advanced React track is included for stronger students.
- **Cohort size:** 2–3 students per GPU workstation. Kensington's five
  machines support **10–15 students per cohort**; Camden (6 machines) and
  Newark (10) support the same or larger.
- **Pilot site:** Kensington, with the curriculum written to run unchanged
  at Camden and Newark (site differences are documented in a hardware
  appendix).
- **Schedule:** four sessions — proposed as one per week, or two half-days —
  dates to be agreed. Module 4 is the long session.

## What Hopeworks would need to provide

1. **The GPU workstations** at the pilot site (Kensington: the five Dell
   Precision 5860s) for the duration, plus permission to install Ubuntu
   Linux on them. Each machine has two drives, so **Windows can be preserved**
   on the other drive; machines remain dual-purpose afterward.
2. **A per-student laptop or desktop** on which students may install free
   software (Python, Git, VS Code — a documented ~15-minute setup sent to
   students ahead of time). No special hardware needed; these machines never
   run AI models themselves.
3. **Network access** between student machines and the workstations on two
   ports (8000/8080) — a pre-flight check with IT, not a project.
4. **An instructor** (plus one preparation afternoon before the first
   session to image machines and pre-download models — checklist provided),
   and a room with a projector.

## Cost and risk

- **Software cost: $0.** All tools (Ubuntu, vLLM, Python, the Qwen AI
  models) are free and open source; models are downloaded once and run
  locally. No subscriptions, no per-use fees, no student accounts.
- **Data stays on-site.** Everything runs on the local network; nothing
  students type is sent to any cloud AI service. The curriculum includes an
  explicit responsible-use lesson (AI limitations, privacy on shared
  machines).
- **Main commitment:** temporarily dedicating the GPU workstations during
  sessions, plus the imaging afternoon. All changes to the machines are
  reversible.

## After the workshop

The materials are deliberately reusable beyond the pilot:

- **Repeatable at every site** — the curriculum is written site-agnostic,
  with per-site hardware notes for Camden and Newark.
- **Self-paced onboarding** — each module stands alone, so future interns
  can work through the materials outside a formal cohort.
- **A permanent Hopeworks AI service** — the natural capstone project: a
  student team applies the same materials to install vLLM on the site's
  PowerEdge R570 server, giving Hopeworks an internal AI endpoint run and
  maintained by interns. *"Deployed an internal AI service"* is a resume
  line, and the workshop is literally its runbook.

## Materials

Everything is complete and published — tutorials, starter and finished code
for both tracks, an instructor run-book with per-session timings and a
failure-mode playbook, a printable command cheat sheet, student pre-reading,
and setup guides:

- Repository: <https://github.com/wbhm/llm-workshop>
- Curriculum overview: <https://github.com/wbhm/llm-workshop/blob/main/README.md>
- Instructor run-book: <https://github.com/wbhm/llm-workshop/blob/main/instructor/run-book.md>
- Student machine setup (sent ahead): <https://github.com/wbhm/llm-workshop/blob/main/appendices/d-student-machine-setup.md>

---

*Questions, scheduling, or a walkthrough of the materials: contact the
workshop organizer.*
