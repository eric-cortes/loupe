from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.orchestrator import run_conversation
from api.previews import get_preview_jpeg

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://archive:archive@localhost:5433/archive"
)
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Archive Curator Chat")


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class Match(BaseModel):
    id: int
    file_path: str
    caption: str | None
    camera_model: str | None
    capture_time: str | None
    rating: int | None
    similarity: float | None
    keywords: list[str]
    collections: list[str]


class ChatResponse(BaseModel):
    answer: str
    structured_calls: list[dict]
    matches: list[Match]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    result = run_conversation([m.model_dump() for m in req.messages])
    return ChatResponse(**result)


@app.get("/images/{image_id}/preview")
def image_preview(image_id: int, size: Literal["thumb", "full"] = "thumb") -> Response:
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT lrcat_id FROM images WHERE id = %s", (image_id,)
        ).fetchone()
    content = get_preview_jpeg(row[0], size) if row and row[0] is not None else None
    if content is None:
        raise HTTPException(status_code=404, detail="No Lightroom preview for this image")
    return Response(
        content=content,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# Registered last so /health and /chat above take precedence; serves the
# Vite-built frontend (frontend/ -> pnpm build -> here) with SPA index fallback.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
