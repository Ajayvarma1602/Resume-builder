#!/usr/bin/env python3
"""
AI Resume Builder — Web Server
Run with: uvicorn app:app --reload --port 8000
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

app = FastAPI()

BASE_DIR = Path(__file__).parent
RESUME_PATH = BASE_DIR / "resume.md"
MAX_ITERATIONS = 10
SCORE_THRESHOLD = 85


class TailorRequest(BaseModel):
    company: str = ""
    role: str = ""
    jd: str


def run_pipeline(company: str, role: str, jd: str, q: Queue):
    try:
        load_dotenv(BASE_DIR / ".env", override=True)
        from tailor_resume import (
            evaluate_resume,
            improve_resume,
            md_to_html,
            research_company,
            tailor_resume,
            upload_to_drive,
        )

        base_resume = RESUME_PATH.read_text()

        # Phase 1: Research
        if company:
            q.put({"type": "status", "step": "research", "message": f"Researching {company}..."})
            research = research_company(company, role)
            q.put({"type": "status", "step": "research", "message": "Company research complete"})
        else:
            q.put({"type": "status", "step": "research", "message": "Skipping — no company provided"})
            research = "No company research available."

        # Phase 2: Tailor
        label = f"{company} · {role}".strip(" ·") or "this role"
        q.put({"type": "status", "step": "tailor", "message": f"Tailoring resume for {label}..."})
        current_resume = tailor_resume(base_resume, jd, research)
        q.put({"type": "status", "step": "tailor", "message": "Resume tailored"})

        # Phases 3+4: Evaluate + Iterate
        final_resume = current_resume
        final_score = None

        for attempt in range(1, MAX_ITERATIONS + 1):
            q.put({"type": "status", "step": "evaluate", "message": f"Scoring resume (attempt {attempt}/{MAX_ITERATIONS})..."})
            evaluation = evaluate_resume(current_resume, jd)
            score = evaluation.get("score", 0)
            weak = evaluation.get("weak", [])
            final_score = score

            if score >= SCORE_THRESHOLD:
                q.put({"type": "score", "score": score, "passed": True, "weak": weak})
                final_resume = current_resume
                break

            q.put({"type": "score", "score": score, "passed": False, "weak": weak})

            if attempt < MAX_ITERATIONS:
                q.put({"type": "status", "step": "improve", "message": f"Rewriting weak sections (round {attempt})..."})
                current_resume = improve_resume(current_resume, evaluation, jd)
                final_resume = current_resume
            else:
                final_resume = current_resume

        # Phase 5: Upload
        q.put({"type": "status", "step": "upload", "message": "Uploading to Google Drive..."})
        html = md_to_html(final_resume)

        timestamp = datetime.now().strftime("%Y-%m-%d")
        parts = [p for p in [company, role] if p]
        doc_name = f"SSK Resume — {' — '.join(parts) if parts else 'Base'} — {timestamp}"

        url = upload_to_drive(html, doc_name)
        q.put({"type": "done", "url": url, "score": final_score})

    except Exception as e:
        q.put({"type": "error", "message": str(e)})
    finally:
        q.put(None)  # sentinel


@app.post("/tailor")
async def tailor(req: TailorRequest):
    if not req.jd.strip():
        return {"error": "Job description is required"}

    q: Queue = Queue()
    thread = Thread(target=run_pipeline, args=(req.company, req.role, req.jd, q), daemon=True)
    thread.start()

    async def stream():
        loop = asyncio.get_event_loop()
        while True:
            msg = await loop.run_in_executor(None, q.get)
            if msg is None:
                break
            yield f"data: {json.dumps(msg)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/", response_class=HTMLResponse)
async def root():
    return (BASE_DIR / "static" / "index.html").read_text()


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
