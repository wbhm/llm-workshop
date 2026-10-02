"""Hopeworks LLM Workshop -- model manager (STARTER).

Your job: complete TODO 1, 2 and 3. Module 5 walks through each one.

A tiny control-plane API that sits NEXT TO vLLM on the GPU server and lets
anyone with the site key see what is on disk, see what is serving, and
switch the served model. vLLM itself has no "load another model" endpoint:
one process serves one model. So "switching" means rewriting the systemd
unit's environment file and restarting the unit.

Run from this directory (inside the ~/vllm-lab venv -- it already has
fastapi, uvicorn, httpx and huggingface_hub):

    MANAGER_API_KEY=<site-key> uvicorn manager:app --host 0.0.0.0 --port 8001 --reload

Settings (all environment variables, all optional):
    MANAGER_API_KEY   bearer token clients must send; unset = no auth (lab only)
    VLLM_ENV_FILE     env file the vllm.service unit reads   (default /etc/vllm/vllm.env)
    VLLM_UNIT         systemd unit name to restart            (default vllm)
    VLLM_URL          where vLLM listens, for health probes   (default http://localhost:8000)
"""

import os
import re
import subprocess
import time

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from huggingface_hub import scan_cache_dir
from pydantic import BaseModel

MANAGER_API_KEY = os.environ.get("MANAGER_API_KEY")
VLLM_ENV_FILE = os.environ.get("VLLM_ENV_FILE", "/etc/vllm/vllm.env")
VLLM_UNIT = os.environ.get("VLLM_UNIT", "vllm")
VLLM_URL = os.environ.get("VLLM_URL", "http://localhost:8000").rstrip("/")

app = FastAPI(title="Hopeworks Model Manager")


# ── auth (done for you) ───────────────────────────────────────────────────
def require_key(authorization: str | None = Header(default=None)) -> None:
    """Same convention as vLLM's --api-key: `Authorization: Bearer <key>`."""
    if MANAGER_API_KEY is None:
        return  # auth disabled
    if authorization != f"Bearer {MANAGER_API_KEY}":
        raise HTTPException(status_code=401, detail="missing or wrong API key")


# ── helpers (done for you) ────────────────────────────────────────────────
def read_env_file() -> dict[str, str]:
    """Parse KEY=value lines from the vLLM unit's environment file."""
    values: dict[str, str] = {}
    try:
        with open(VLLM_ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    values[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return values


def write_env_value(key: str, value: str) -> None:
    """Replace (or append) one KEY=value line, leaving everything else intact."""
    try:
        with open(VLLM_ENV_FILE) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        lines = []
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    new_line = f"{key}={value}"
    if any(pattern.match(line) for line in lines):
        lines = [new_line if pattern.match(line) else line for line in lines]
    else:
        lines.append(new_line)
    with open(VLLM_ENV_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")


def unit_state() -> str:
    """active / inactive / failed / activating ... as systemd reports it."""
    result = subprocess.run(
        ["systemctl", "is-active", VLLM_UNIT], capture_output=True, text=True
    )
    return result.stdout.strip() or "unknown"


def vllm_ready() -> tuple[bool, list[str]]:
    """Probe vLLM: is it answering, and which model ids does it report?"""
    headers = {}
    key = read_env_file().get("VLLM_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        r = httpx.get(f"{VLLM_URL}/v1/models", headers=headers, timeout=2.0)
        if r.status_code == 200:
            return True, [m["id"] for m in r.json().get("data", [])]
    except httpx.HTTPError:
        pass
    return False, []


# ── endpoints (your work) ─────────────────────────────────────────────────
@app.get("/models", dependencies=[Depends(require_key)])
def list_models():
    """What could we serve? (Everything in the local HuggingFace cache.)"""
    # ── TODO 1 ──────────────────────────────────────────────────────────
    # Return {"models": [{"id": "Qwen/Qwen2.5-7B-Instruct", "size_gb": 15.2}, ...]}
    # for every MODEL repo in the HuggingFace cache.
    #
    # Hints:
    #   - `scan_cache_dir()` is the library version of `hf cache scan`
    #     (Module 3 §4). It returns an object with a `.repos` set.
    #   - each repo has `.repo_id`, `.repo_type` ("model"/"dataset"/...)
    #     and `.size_on_disk` in bytes
    #   - sort by id so the list is stable
    # ────────────────────────────────────────────────────────────────────
    return {"models": []}  # replace me


@app.get("/status", dependencies=[Depends(require_key)])
def status():
    """What is configured, is the unit up, and is vLLM actually answering?"""
    # ── TODO 2 ──────────────────────────────────────────────────────────
    # Return four facts, using the helpers above:
    #   "configured_model": the MODEL line of the env file (read_env_file)
    #   "unit":             systemd's word for the unit (unit_state)
    #   "ready":            is vLLM answering /v1/models?   (vllm_ready)
    #   "serving":          the model ids vLLM reports      (vllm_ready)
    # "configured" and "serving" differ for 1-3 minutes after a switch --
    # that gap is the whole reason this endpoint exists.
    # ────────────────────────────────────────────────────────────────────
    return {"configured_model": None, "unit": "unknown", "ready": False, "serving": []}


class SwitchRequest(BaseModel):
    model: str
    wait: bool = False  # block until vLLM is answering again (up to 5 min)


@app.post("/switch", dependencies=[Depends(require_key)])
def switch(req: SwitchRequest):
    """Point the vllm unit at a different cached model and restart it."""
    # ── TODO 3 ──────────────────────────────────────────────────────────
    # 1. Refuse (HTTPException 400) if req.model is not in the cache --
    #    reuse your TODO 1 code. Tell the caller to `hf download` it.
    # 2. write_env_value("MODEL", req.model)
    # 3. Restart the unit WITHOUT a password prompt:
    #       subprocess.run(["sudo", "-n", "systemctl", "restart", VLLM_UNIT],
    #                      capture_output=True, text=True)
    #    If .returncode != 0 -> HTTPException 500 with .stderr
    #    (the sudoers rule in deploy/ is what makes -n work)
    # 4. If not req.wait: return {"status": "restarting", "model": ..., "poll": "/status"}
    # 5. If req.wait: loop up to 300 s: every 3 s call vllm_ready(); return
    #    {"status": "ready", "model": ...} once req.model is in `serving`.
    #    If unit_state() == "failed" -> HTTPException 500 pointing at
    #    `journalctl -u vllm -n 50`. After 300 s -> HTTPException 504.
    # ────────────────────────────────────────────────────────────────────
    raise HTTPException(status_code=501, detail="TODO 3 not implemented yet")
