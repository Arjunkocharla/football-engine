"""HTTP v1 router composition."""

from fastapi import APIRouter

from football_engine.api.http.v1.routes.event_routes import events_router
from football_engine.api.http.v1.routes.match_routes import matches_router
from football_engine.api.http.v1.routes.system_routes import system_router

api_v1_router = APIRouter()
api_v1_router.include_router(system_router)
api_v1_router.include_router(matches_router)
api_v1_router.include_router(events_router)
