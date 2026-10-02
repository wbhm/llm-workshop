# Module 5 — A Permanent Server: systemd and a Model-Switching API

| | |
|---|---|
| **Time** | ~3 hours |
| **You start with** | Modules 1–4 complete, **sudo on the site's PowerEdge R570** (NVIDIA L4, 24 GB), Ubuntu + NVIDIA driver already on it, vLLM installed there per Module 1 §4–5 |
| **You end with** | vLLM running as a boot-time service with an API key, two models on disk, and a small API *you wrote* that switches which model is served |
| **Works solo?** | Yes — this module is designed as a post-workshop project for one or two interns |

## What you'll learn

- Why "run it in tmux" is not a deployment, and what **systemd** does instead
- Environment files: separating *configuration* from the *service definition*
- Why vLLM cannot hot-swap models — and how production teams switch anyway
- Giving a program *one* root privilege, precisely, with **sudoers**
- Building a control-plane API with FastAPI (same skills as Module 4)

*New jargon along the way? Every term is defined in the
[Glossary](../appendices/e-glossary.md).*

> **Where does this run?** Modules 1–4 used the workstations. This module
> targets the **R570 rack server** in the Camden and Kensington racks
> ([Appendix A](../appendices/a-hardware-profiles.md)). Its L4 has 24 GB,
> half a workstation GPU — enough for one 7B model at a time, which is the
> whole reason a *switcher* is worth building. Everything here also works
> on a workstation if you want to practice first.

---

## 0. State check

SSH to the R570 (ask your instructor for the address and the `hopeworks`
password) and run:

```bash
nvidia-smi                              # one "NVIDIA L4", ~0 MiB used
cd ~/vllm-lab && source .venv/bin/activate
vllm --version                          # prints a version
hf cache scan                           # may be empty — that's fine
```

If `vllm` is missing, do Module 1 §4–5 on this machine first (10 minutes).
If `nvidia-smi` fails, stop and get IT — the driver is their step here.

---

## 1. Concept: a process vs. a service

In Module 2 you started vLLM in a tmux pane. Close the laptop, lose the SSH
session, reboot the box — the server is gone. That's a *process*. A
*service* is a process the operating system owns: started at boot, restarted
on crash, logs collected, controlled with one command. On Ubuntu the thing
that does this is **systemd**, and a service is described by a **unit
file**.

```
tmux pane            →   lives as long as your login
systemd unit         →   lives as long as the machine
```

The second idea is *where the settings go*. Hard-coding the model name
inside the unit file means editing a root-owned file on every switch.
Instead the unit reads an **environment file** (`/etc/vllm/vllm.env`) —
plain `KEY=value` lines. Change the file, restart the unit, new model. Your
API in §5 will do exactly that.

---

## 2. Download the models you'll switch between

Both ungated, both ~15 GB, both fit the L4 one at a time:

```bash
hf download Qwen/Qwen2.5-Coder-7B-Instruct    # tuned for code — the VS Code model
hf download Qwen/Qwen2.5-7B-Instruct          # the workshop chat model
hf cache scan
df -h /                                        # ≥ 40 GB free is comfortable
```

**✅ Checkpoint:** `hf cache scan` lists both.

> 💡 **Why not run both at once?** Two × 15 GB of weights on a 24 GB card.
> Module 2's rule of thumb (2 GB per billion parameters) says no before you
> try. On the 48 GB workstations you *could*; here you switch.

---

## 3. vLLM as a systemd service

The files are in `code/finished/model-manager/deploy/`. Get the workshop
code onto the R570 (`git clone` it, or `scp` the folder), then:

### 3a. The environment file

```bash
sudo mkdir -p /etc/vllm
sudo cp deploy/vllm.env.example /etc/vllm/vllm.env
sudo chown hopeworks:hopeworks /etc/vllm /etc/vllm/vllm.env
sudo chmod 640 /etc/vllm/vllm.env
nano /etc/vllm/vllm.env          # set VLLM_API_KEY to the site key
```

Read it — three settings, each a Module 2 idea:

```ini
MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
MAX_MODEL_LEN=32768
VLLM_API_KEY=<the site key>
```

`MAX_MODEL_LEN=32768` is bigger than the workshop's 8192 because a coding
assistant stuffs whole files into the prompt. It still fits: a 7B model's
KV cache costs ~56 KB per token, and the L4 has ~5 GB left after weights —
the startup log tells you exactly how many tokens that bought.

> ⚠️ **The key is a secret.** `chmod 640` + owner `hopeworks` means only
> that account (and root) can read it. Never paste it into a chat log, a
> commit, or a frontend.

### 3b. The unit file

```bash
sudo cp deploy/vllm.service /etc/systemd/system/vllm.service
sudo systemctl daemon-reload            # "I changed a unit file, re-read them"
sudo systemctl enable --now vllm        # start now AND at every boot
journalctl -u vllm -f                   # the same startup logs as Module 2, Ctrl-C to stop watching
```

Open `vllm.service` and match it to what you know:

| Line | Module 2 equivalent |
|---|---|
| `ExecStart=.../vllm serve ${MODEL} --port 8000 ...` | the `vllm serve` command you typed |
| `EnvironmentFile=/etc/vllm/vllm.env` | where `${MODEL}` etc. come from |
| `--api-key ${VLLM_API_KEY}` | the "real deployment" flag from §5 |
| `--enable-auto-tool-choice --tool-call-parser hermes` | new: lets the model *call tools* — VS Code agents need it |
| `Restart=on-failure` | you, re-running the command after a crash |
| `User=hopeworks` | never run a network service as root |

Four commands you now own:

```bash
systemctl status vllm        # running? since when? last log lines
sudo systemctl restart vllm  # re-read env file, reload model (1–3 min)
sudo systemctl stop vllm     # free the GPU
journalctl -u vllm -n 100    # last 100 log lines
```

### 3c. Prove it — with the key

```bash
export VLLM_API_KEY=<the site key>
curl -s http://localhost:8000/v1/models | jq            # → 401 Unauthorized. Good.
curl -s http://localhost:8000/v1/models \
  -H "Authorization: Bearer $VLLM_API_KEY" | jq -r '.data[].id'
```

**✅ Checkpoint:** the first curl is refused, the second prints
`Qwen/Qwen2.5-Coder-7B-Instruct`. Now `sudo reboot`, wait two minutes, and
run the second curl again *without starting anything*. That's the
difference between a process and a service.

---

## 4. Switching by hand (so you know what you're automating)

```bash
sed -i 's|^MODEL=.*|MODEL=Qwen/Qwen2.5-7B-Instruct|' /etc/vllm/vllm.env
sudo systemctl restart vllm
watch -n 2 'curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health'
```

Watch the health code go `000` (down) → `200` (up); it takes 1–3 minutes
while 15 GB loads. Then confirm with `/v1/models`. Switch back the same way.

Three steps: **edit the file, restart the unit, wait for health.** That's
the entire algorithm of the API you're about to write. Do it by hand twice
so the automation is boring.

> **🎓 Instructor:** this is the moment to ask *why vLLM doesn't just offer
> `POST /v1/load_model`*. (Loading weights is seconds-to-minutes and holds
> the whole GPU; serving engines keep that decision outside the request
> path. Production teams run a router in front of several engines — the
> switcher you build is the one-GPU version of that idea.)

---

## 5. Build the model manager (TODOs 1–3)

Open `code/starter/model-manager/manager.py` in VS Code. The auth
dependency and four helper functions are written for you — read them first;
each is a Module 3 command turned into Python:

| Helper | The command it replaces |
|---|---|
| `read_env_file()` / `write_env_value()` | `cat` / `sed -i` on `/etc/vllm/vllm.env` |
| `unit_state()` | `systemctl is-active vllm` |
| `vllm_ready()` | `curl -H "Authorization: Bearer ..." :8000/v1/models` |

Run it on the R570 in a second SSH session, in the same venv as vLLM (it
already has FastAPI — no installs):

```bash
cd ~/llm-workshop/code/starter/model-manager
source ~/vllm-lab/.venv/bin/activate
MANAGER_API_KEY=$VLLM_API_KEY uvicorn manager:app --host 0.0.0.0 --port 8001 --reload
```

From your laptop (or another SSH window), you'll test with:

```bash
export MGR=http://<R570_IP>:8001
export AUTH="Authorization: Bearer <the site key>"
```

### TODO 1 — `GET /models`: what *could* we serve?

Module 3 §4's `hf cache scan`, as a function. `scan_cache_dir()` from
`huggingface_hub` returns an object whose `.repos` holds one entry per
cached repo, with `.repo_id`, `.repo_type` and `.size_on_disk`. Return the
model repos as `{"id": ..., "size_gb": ...}`, sorted by id.

```bash
curl -s $MGR/models -H "$AUTH" | jq
curl -s $MGR/models | jq            # no key → 401 (the dependency does this for you)
```

**✅ Checkpoint:** both Qwen models listed with sizes around 15 GB.

### TODO 2 — `GET /status`: what *is* being served?

Four facts, all from helpers: the `MODEL` line of the env file, the unit
state, whether vLLM answers, and which model ids it reports. Why both
"configured" and "serving"? Because for 1–3 minutes after a switch they
*disagree* — and that gap is what a client needs to see.

```bash
curl -s $MGR/status -H "$AUTH" | jq
```

**✅ Checkpoint:** `"ready": true` and `serving` matches `configured_model`.
Now `sudo systemctl stop vllm` and call it again — `"unit": "inactive"`,
`"ready": false`. Start it again.

### TODO 3 — `POST /switch`: the payoff

The §4 algorithm, with guard rails:

1. **Validate** — if the requested model isn't in the cache, answer `400`
   and tell the caller to `hf download` it. (Reuse TODO 1.)
2. **Edit** — `write_env_value("MODEL", req.model)`.
3. **Restart** — `subprocess.run(["sudo", "-n", "systemctl", "restart", VLLM_UNIT], ...)`.
   `-n` means "never prompt for a password". That works only because of the
   sudoers rule in §6; until you install it this step returns a non-zero
   code and you should surface `stderr` as a `500`.
4. **Reply** — `{"status": "restarting", "poll": "/status"}`, or if the
   caller sent `"wait": true`, poll `vllm_ready()` every 3 s for up to
   5 minutes and reply `"ready"` once the new model id appears. Raise a
   `500` if `unit_state()` turns `failed`, `504` on timeout.

Install the sudoers rule first (§6), then:

```bash
curl -s -X POST $MGR/switch -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-7B-Instruct", "wait": true}'
curl -s $MGR/status -H "$AUTH" | jq .serving
```

**✅ Checkpoint:** a model switch from your laptop, no SSH, in one request.
Try a model that isn't cached and read the `400`.

Compare with `code/finished/model-manager/manager.py` when done.

---

## 6. One root privilege, precisely: sudoers

The manager runs as `hopeworks` but must restart a root-owned service. The
wrong fix is running the manager as root. The right fix is a **sudoers**
rule granting *that user* *those commands* *without a password* — and
nothing else:

```bash
cat deploy/sudoers-vllm-manager
sudo visudo -c -f deploy/sudoers-vllm-manager        # syntax check FIRST
sudo install -m 0440 deploy/sudoers-vllm-manager /etc/sudoers.d/vllm-manager
sudo -n systemctl restart vllm && echo "no password needed"
sudo -n apt update || echo "and nothing else works — correct"
```

> ⚠️ A sudoers file with a typo can lock *everyone* out of sudo. That's why
> the check runs before the install, every time.

---

## 7. Make the manager a service too

Same recipe as §3:

```bash
mkdir -p ~/model-manager
cp manager.py ~/model-manager/              # your finished version
sudo cp deploy/model-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now model-manager
curl -s http://localhost:8001/status -H "$AUTH" | jq
```

**✅ Checkpoint:** reboot the R570 one last time. Two minutes later, both
`:8000/v1/models` (with key) and `:8001/status` (with key) answer, and
nobody logged in. **You deployed an internal AI service.**

---

## Wrap-up: what you can now do

- [x] Explain process vs. service, and read a systemd unit file
- [x] Keep configuration in an environment file and reload it with a restart
- [x] Explain why vLLM serves one model per process, and how to switch anyway
- [x] Grant a single root command with sudoers, safely
- [x] Build and deploy a small control-plane API

### Check your understanding

1. The env file says `MODEL=A` but `/status` reports `serving: ["B"]`.
   What happened, and is anything wrong?
2. Why does `/switch` refuse models that aren't cached, instead of
   downloading them for you? Name one cost of each design.
3. What does `sudo -n` do, and what makes it succeed for `systemctl restart
   vllm` but fail for `apt update`?
4. Your laptop's chatbot (Module 4) and VS Code (the setup guide) both
   point at the R570. You switch models. What breaks in each client, and how
   does the model manager's `/status` help?

(Answers are in the instructor run-book.)

**Next:** connect a coding assistant to your server —
[Intern Dev Setup guide §6](../guides/intern-dev-setup.md#6-connect-vs-code-continue-to-the-server-10-min).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `systemctl status vllm` → `failed`, log says CUDA out of memory | A stray `vllm serve` (tmux!) still holds the GPU | `nvidia-smi` → kill it; `pkill -f "vllm serve"`; restart the unit |
| Unit starts but `/v1/models` → 401 even with the key | Shell variable not exported, or quotes around the key in the env file | `echo $VLLM_API_KEY`; env file lines are `KEY=value`, no quotes |
| `/switch` → 500 `sudo: a password is required` | sudoers rule not installed, or wrong path to `systemctl` | §6; `which systemctl` must match the rule (`/usr/bin/systemctl`) |
| `/switch` → 400 "not in the cache" for a model you downloaded | Downloaded as a different user, so a different cache | `hf cache scan` *as hopeworks*; `HF_HOME` must match between shell and unit |
| `/status` says `activating` for a long time | Normal: 15 GB weight load + graph capture | 1–3 min; `journalctl -u vllm -f` shows progress |
| Switch "worked" but VS Code / chatbot errors | Clients cache the old model id | Re-select the model in Continue; refresh the chatbot (it re-reads `/api/models`) |
| Laptop can't reach `:8001` but `:8000` works | Firewall only opened for vLLM | IT needs 8001 too; `sudo ufw status` on the R570 |
