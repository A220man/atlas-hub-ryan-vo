from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import health, auth, presentations, evaluation, narration, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce runtime production guardrails
    settings.validate_runtime_guards()
    # Initialize database tables
    init_db()
    yield


def create_app() -> FastAPI:
    """Application factory for Atlas Hub."""
    application = FastAPI(
        title="Atlas Hub — Presentation Synthesis & Alignment Evaluation Platform",
        description="Turns technical documents into structured native PowerPoint decks with span-level attribution integrity and multi-modal alignment evaluation.",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # CORS Middleware configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    application.include_router(health.router, prefix="/api")
    application.include_router(auth.router, prefix="/api")
    application.include_router(presentations.router, prefix="/api")
    application.include_router(evaluation.router, prefix="/api")
    application.include_router(narration.router, prefix="/api")
    application.include_router(templates.router, prefix="/api")

    return application


app = create_app()
