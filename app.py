from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import uuid
from core.generator import run

app = FastAPI()
JOBS = {}

class Config(BaseModel):
    chunks: List[str]
    tasks: List[str] = ["qa", "instruction"]
    difficulties: List[str] = ["medium"]
    samples_per_chunk: int = 5
    apply_filter: bool = True

@app.post("/generate")
async def generate(cfg: Config, bg: BackgroundTasks):
    jid = uuid.uuid4().hex[:8]
    JOBS[jid] = {"status": "running", "stats": {}}
    bg.add_task(_run, jid, cfg)
    return {"job_id": jid}

async def _run(jid, cfg):
    try:
        stats, train, val = await run(jid, cfg.chunks, cfg.tasks, cfg.difficulties, cfg.samples_per_chunk, cfg.apply_filter)
        JOBS[jid].update({"status": "done", "stats": stats, "train": train, "val": val})
    except Exception as e:
        JOBS[jid].update({"status": "failed", "error": str(e)})

@app.get("/status/{jid}")
async def status(jid: str):
    if jid not in JOBS: raise HTTPException(404)
    return JOBS[jid]

@app.get("/download/{jid}")
async def download(jid: str, split: str = "train"):
    if jid not in JOBS: raise HTTPException(404)
    p = JOBS[jid].get(f"{split}")
    if not p: raise HTTPException(404, "not ready")
    return FileResponse(p, filename=p.split("/")[-1])

@app.get("/")
async def root():
    return {"status": "ok", "jobs": list(JOBS.keys())}
