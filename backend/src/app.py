"""FastAPI application factory.

Its only job is composition: build the app, wire CORS, mount module routers and
register module exception handlers. No business logic ever lands here.

This is now the SINGLE application. `main.py` is a thin entry point that
imports `create_app()` — previously it built a second, separate app that
mounted only Career Recommendation, so the two modules could never see
each other.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.career_recommendation.api import router as career_recommendation_router
from src.career_report import register_career_report
from src.core.config import get_settings
from src.cv_review import register_cv_review
from src.feedback import register_feedback
from src.job_discovery_matching import (
    ensure_checkpointer_tables,
    register_job_discovery,
)
from src.resume_parsing import register_resume_parsing

logger = logging.getLogger(__name__)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@asynccontextmanager
async def _lifespan(app: FastAPI):
    try:
        await ensure_checkpointer_tables()
    except Exception:
        logger.exception(
            "Failed to set up LangGraph checkpoint tables — job discovery's "
            "query/judge confirmation steps will fail until this is fixed."
        )
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = FastAPI(
        title="DiscoverMyRole — Intelligent Career Navigation System API",
        version="1.0.0",
        debug=settings.debug,
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    register_resume_parsing(app)
    app.include_router(career_recommendation_router)
    register_job_discovery(app)
    register_career_report(app)
    register_cv_review(app)
    register_feedback(app)
    return app