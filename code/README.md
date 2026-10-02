# Workshop Code

Two trees, same layout:

- **`starter/`** — skeletons with numbered `TODO` markers. Students work here;
  [Module 4](../modules/module-4-chatbot.md) walks through every TODO.
- **`finished/`** — complete reference implementations. For instructors,
  for stuck students to *compare against* (not copy from), and for anyone
  who wants a working chatbot immediately.

## Layout

```
backend/          FastAPI app: proxies + streams between browser and vLLM
                  TODOs 1-3 (starter)
frontend-html/    Beginner track: vanilla HTML/CSS/JS chat UI
                  TODOs 4-6 (starter)
frontend-react/   Advanced track: same app in React (Vite)
                  TODOs R1-R3 (starter)
model-manager/    Module 5: control-plane API that switches the served model
                  TODOs 1-3 (starter); deploy/ holds systemd units + sudoers rule
```

## Quick start (finished version)

With a vLLM server already running (Modules 1–2):

```bash
cd finished/backend
python -m venv .venv && source .venv/bin/activate   # or: uv venv --seed && source .venv/bin/activate
pip install -r requirements.txt

# vLLM on the same machine:
uvicorn app:app --host 0.0.0.0 --port 8080

# vLLM on another machine:
VLLM_BASE_URL=http://<workstation-ip>:8000/v1 uvicorn app:app --host 0.0.0.0 --port 8080

# a server started with --api-key (the R570, Module 5):
VLLM_BASE_URL=http://<r570-ip>:8000/v1 VLLM_API_KEY=<site-key> uvicorn app:app --host 0.0.0.0 --port 8080
```

Open `http://localhost:8080/` — the backend serves the beginner frontend
itself. Done.

**React track:**

```bash
cd finished/frontend-react
npm install
npm run dev        # dev server on http://localhost:5173, proxies /api to :8080
```

The backend must also be running (it's the same one for both tracks).
