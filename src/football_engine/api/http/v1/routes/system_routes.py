"""System and health endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from football_engine.api.dependencies.session import get_db

system_router = APIRouter(tags=["system"])


@system_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@system_router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness: checks DB connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
