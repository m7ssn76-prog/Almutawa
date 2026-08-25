from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from world import InteractiveDigitalWorld

ROOT = Path(__file__).resolve().parent


class CommandRequest(BaseModel):
    command: str = Field(min_length=2, max_length=40)


class TickRequest(BaseModel):
    seconds: int = Field(default=1, ge=1, le=600)


def create_app(runtime: Path | None = None) -> FastAPI:
    runtime_dir = runtime or Path(os.getenv("IDW_RUNTIME", str(ROOT / "runtime")))
    world = InteractiveDigitalWorld(runtime_dir)
    app = FastAPI(title="Interactive Digital World", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return (ROOT / "static" / "index.html").read_text(encoding="utf-8")

    @app.get("/api/state")
    def get_state() -> dict:
        return world.snapshot()

    @app.post("/api/command")
    def command(request: CommandRequest) -> dict:
        try:
            return world.apply_command(request.command)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/tick")
    def tick(request: TickRequest) -> dict:
        try:
            return world.tick(request.seconds)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/events")
    def events(limit: int = 30) -> list[dict]:
        limit = max(1, min(100, limit))
        path = world.events.path
        if not path.exists():
            return []
        import json

        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows[-limit:]

    @app.get("/health")
    def health() -> dict:
        valid, count = world.events.verify()
        return {
            "status": "ok" if valid else "degraded",
            "classification": "Internal Test Only",
            "simulation_only": True,
            "real_environment_connected": False,
            "evidence_chain_valid": valid,
            "evidence_events": count,
        }

    return app


app = create_app()
