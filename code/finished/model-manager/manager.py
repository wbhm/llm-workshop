"""Hopeworks LLM Workshop -- model manager (finished reference).

A tiny control-plane API that sits NEXT TO vLLM on the GPU server and lets
anyone with the site key see what is on disk, see what is serving, and
switch the served model. vLLM itself has no "load another model" endpoint:
one process serves one model. So "switching" means rewriting the systemd
unit's environment file and restarting the unit -- which is exactly what
this service does.

Run from this directory (inside the ~/vllm-lab venv -- it already has
fastapi, uvicorn, httpx and huggingface_hub):

    MANAGER_API_KEY=<site-key> uvicorn manager:app --host 0.0.0.0 --port 8001

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


# ── auth ──────────────────────────────────────────────────────────────────
def require_key(authorization: str | None = Header(default=None)) -> None:
    """Same convention as vLLM's --api-key: `Authorization: Bearer <key>`."""
    if MANAGER_API_KEY is None:
        return  # auth disabled
    if authorization != f"Bearer {MANAGER_API_KEY}":
        raise HTTPException(status_code=401, detail="missing or wrong API key")


# ── helpers ───────────────────────────────────────────────────────────────
def cached_models() -> list[dict]:
    """Models already downloaded into the HuggingFace cache on this machine."""
    info = scan_cache_dir()  # honours HF_HOME, same cache `hf cache scan` shows
    return sorted(
        (
            {"id": repo.repo_id, "size_gb": round(repo.size_on_disk / 1e9, 1)}
            for repo in info.repos
            if repo.repo_type == "model"
        ),
        key=lambda m: m["id"],
    )


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


# ── endpoints ─────────────────────────────────────────────────────────────
@app.get("/models", dependencies=[Depends(require_key)])
def list_models():
    """What could we serve? (Everything in the local HuggingFace cache.)"""
    return {"models": cached_models()}


@app.get("/status", dependencies=[Depends(require_key)])
def status():
    """What is configured, is the unit up, and is vLLM actually answering?"""
    ready, serving = vllm_ready()
    return {
        "configured_model": read_env_file().get("MODEL"),
        "unit": unit_state(),
        "ready": ready,
        "serving": serving,
    }


class SwitchRequest(BaseModel):
    model: str
    wait: bool = False  # block until vLLM is answering again (up to 5 min)


@app.post("/switch", dependencies=[Depends(require_key)])
def switch(req: SwitchRequest):
    """Point the vllm unit at a different cached model and restart it."""
    available = {m["id"] for m in cached_models()}
    if req.model not in available:
        raise HTTPException(
            status_code=400,
            detail=f"{req.model!r} is not in the cache. Download it first: "
            f"hf download {req.model}. Cached: {sorted(available)}",
        )

    write_env_value("MODEL", req.model)

    # -n = never prompt for a password. The sudoers rule in deploy/ allows
    # exactly this command and nothing else.
    result = subprocess.run(
        ["sudo", "-n", "systemctl", "restart", VLLM_UNIT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr.strip())

    if not req.wait:
        return {"status": "restarting", "model": req.model, "poll": "/status"}

    deadline = time.time() + 300
    while time.time() < deadline:
        ready, serving = vllm_ready()
        if ready and req.model in serving:
            return {"status": "ready", "model": req.model}
        if unit_state() == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"{VLLM_UNIT} failed to start -- journalctl -u {VLLM_UNIT} -n 50",
            )
        time.sleep(3)
    raise HTTPException(status_code=504, detail="timed out waiting for vLLM")
