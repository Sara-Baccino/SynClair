"""
synclair_gui.app
--------------------

FastAPI entry point. Wires together CORS, lifespan, and the domain
routers (auth, datasets, structure, demo). Contains no business logic:
it only orchestrates wiring -- StructureModule/DataConfig/AnalysisResult
are never touched here directly, only inside the routers/services.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from synclair_gui.routers import auth, datasets, demo, structure

from fastapi.middleware.cors import CORSMiddleware



__all__ = ["app", "create_app"]

_DEFAULT_DEV_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


def _resolve_allowed_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", _DEFAULT_DEV_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    application = FastAPI(
        title="SynClair API",
        description="Backend API for the SynClair data intelligence workspace.",
        version="0.1.0",
        lifespan=_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_resolve_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(auth.router)
    application.include_router(datasets.router)
    application.include_router(structure.router)
    application.include_router(demo.router)

    @application.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://synclair.vercel.app"],  # Il tuo URL frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)