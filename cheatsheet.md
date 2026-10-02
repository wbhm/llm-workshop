# LLM Workshop Cheat Sheet

*Every command from the workshop, one page. `<IP>` = a GPU workstation's address.*

## Environment (start of every terminal session)

```bash
cd ~/vllm-lab && source .venv/bin/activate
```

## GPU

```bash
nvidia-smi                  # GPU status: memory, utilization, processes
watch -n 1 nvidia-smi       # ...refreshing live
nvtop                       # nicer live view
```

## Models on disk

```bash
hf download Qwen/Qwen2.5-7B-Instruct    # fetch (resumes if interrupted)
hf cache scan                           # what's cached, how big
hf cache delete                         # interactive cleanup
df -h /                                 # disk space left
```

## Serve

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct --max-model-len 4096   # small/fast
vllm serve Qwen/Qwen2.5-7B-Instruct  --max-model-len 8192    # workhorse
# useful flags:
#   --port 8001                    second server
#   --gpu-memory-utilization 0.5   use half the VRAM
#   --api-key <secret>             require auth
# dual-GPU boxes (Kensington/Camden):
CUDA_VISIBLE_DEVICES=1 vllm serve <model> --port 8001
vllm serve <model> --tensor-parallel-size 2
```

Server is up when logs say `Application startup complete`. Stop: `Ctrl-C`.
Stale server holding the port: `pkill -f "vllm serve"`.

## Query the API

```bash
curl -s http://<IP>:8000/v1/models | jq -r '.data[].id'     # list models

curl -s http://<IP>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-7B-Instruct",
       "messages":[{"role":"user","content":"Hello!"}]}' \
  | jq -r '.choices[0].message.content'                     # ask, get text

# streaming (raw SSE):  add "stream": true  and curl -N
```

## Built-in clients

```bash
vllm chat                                      # interactive (Ctrl-D exits)
vllm chat --system-prompt "You are a pirate."  # with persona
vllm chat --quick "one-shot question"          # ask and exit
vllm chat --url http://<IP>:8000/v1            # someone else's server
vllm complete --quick "raw text to continue"   # no chat formatting
```

## Monitor

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://<IP>:8000/health   # 200 = alive
curl -s http://<IP>:8000/metrics | grep vllm:num_requests          # load
```

## tmux (server in one pane, commands in another)

```
tmux new -s work      start        Ctrl-b %     split vertical
Ctrl-b "  split horizontal         Ctrl-b ←→↑↓  move panes
Ctrl-b d  detach (keeps running)   tmux attach -t work   return
```

## Chatbot (Module 4)

*Windows: run all of this in **Git Bash**, not PowerShell/cmd.*

```bash
# backend (from code dir):
cd backend && source .venv/bin/activate     # Windows: source .venv/Scripts/activate
VLLM_BASE_URL=http://<IP>:8000/v1 uvicorn app:app --host 0.0.0.0 --port 8080 --reload
# → open http://localhost:8080/

# React track:
cd frontend-react && npm install && npm run dev     # → http://localhost:5173
```

## When things break

| Check | Command |
|---|---|
| Is the GPU alive? | `nvidia-smi` |
| Is my venv active? | prompt shows `(.venv)` — else `source .venv/bin/activate` |
| Is vLLM up? | `curl http://localhost:8000/v1/models` |
| Reachable from here? | `curl http://<IP>:8000/v1/models` |
| Is it DNS? | `ping 1.1.1.1` works but names don't → yes, it's DNS |
| What's on port 8000? | `pkill -f "vllm serve"` to clear a stale server |

## R570 server (Module 5 / intern setup) — needs the site key

```bash
export AUTH="Authorization: Bearer <SITE_KEY>"
curl -s http://<R570_IP>:8000/v1/models -H "$AUTH" | jq -r '.data[].id'   # what's live
curl -s http://<R570_IP>:8001/models -H "$AUTH" | jq                      # what's on disk
curl -s http://<R570_IP>:8001/status -H "$AUTH" | jq                      # unit + ready?
curl -s -X POST http://<R570_IP>:8001/switch -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"model":"Qwen/Qwen2.5-7B-Instruct","wait":true}'
# on the server itself:
systemctl status vllm model-manager      journalctl -u vllm -n 100
sudo systemctl restart vllm              nano /etc/vllm/vllm.env
# chatbot backend against it:
VLLM_BASE_URL=http://<R570_IP>:8000/v1 VLLM_API_KEY=<SITE_KEY> uvicorn app:app --port 8080
```

**Debug order (Module 4):** browser → backend → vLLM. Find which arrow is
broken: dev tools (F12) Network tab for the first arrow, `curl :8080/api/models`
for the second, `curl :8000/v1/models` for the third.
