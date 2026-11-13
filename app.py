import os
import json
import uuid
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, SecretStr
from jsonschema import Draft202012Validator, SchemaError

from core.generator import generate

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
JOBS = {}
app = FastAPI(title="Dataset Generator")

class Settings(BaseModel):
    brief: str = Field(min_length=10, max_length=10000)
    source: str = Field(min_length=1, max_length=2000000)
    api_key: SecretStr = SecretStr("")
    model: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9._-]+$")
    count: int = Field(default=20, ge=1, le=1000)
    format: Literal["messages", "instruction", "custom"] = "messages"
    schema_text: str = Field(default="", max_length=20000)

@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")

@app.post("/api/generate")
async def start(settings: Settings, background: BackgroundTasks):
    if not settings.source.strip() or not settings.brief.strip():
        raise HTTPException(400, "Provide source text and dataset requirements.")
    key = settings.api_key.get_secret_value().strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise HTTPException(400, "Enter your Gemini API key or set GEMINI_API_KEY.")
    schema = None
    if settings.format == "custom":
        try:
            schema = json.loads(settings.schema_text)
            Draft202012Validator.check_schema(schema)
            if not isinstance(schema, dict) or schema.get("type") != "object" or "$ref" in settings.schema_text or "$dynamicRef" in settings.schema_text:
                raise ValueError("Use an object schema without external references.")
        except (ValueError, SchemaError) as exc:
            raise HTTPException(400, "Invalid JSON schema. Use an object schema without references.") from exc
    if any(job["status"] == "running" for job in JOBS.values()):
        raise HTTPException(409, "A dataset is already being generated. Wait for it to finish.")
    job_id = uuid.uuid4().hex
    job = {"status": "running", "requested": settings.count, "accepted": 0, "rejected": 0, "attempts": 0, "preview": [], "error": ""}
    JOBS[job_id] = job
    background.add_task(generate, settings, key, schema, DATA / job_id, job)
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}")
def status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found. Job history resets when the server restarts.")
    return JOBS[job_id].copy()

@app.get("/api/jobs/{job_id}/download")
def download(job_id: str):
    job = status(job_id)
    path = DATA / job_id / "dataset.jsonl"
    if job["status"] == "running" or not path.exists() or not job["accepted"]:
        raise HTTPException(404, "No dataset is ready to download.")
    return FileResponse(path, filename=f"dataset_{job_id}.jsonl", media_type="application/x-ndjson")
