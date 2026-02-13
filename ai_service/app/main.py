"""
Application entry point.

Responsibility:
    Creates and configures the FastAPI application instance.
    Registers routers, middleware, and startup/shutdown events.
    This is the only file that "wires everything together".

Future extension points:
    - Add CORS middleware
    - Add request-id middleware for tracing
    - Register additional API version routers (v2, v3…)
    - Add startup hooks (e.g. warm up AI model, open DB pool)
"""

import os
import sys


from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.v1.cards import router as cards_router
from app.core.config import settings
from app.utils.logger import logger
from fastapi.middleware.cors import CORSMiddleware 


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered flashcard generation microservice.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CROS Middleware  
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(cards_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exeption_handler(request:Request,exc:RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail":exc.errors(),"type":"validation_error"}
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns service health status. Use for liveness probes.",
)
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Startup / shutdown events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    """Runs once when the application starts."""
    logger.info("%s v%s is starting up", settings.APP_NAME, settings.APP_VERSION)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Runs once when the application shuts down."""
    logger.info("%s is shutting down", settings.APP_NAME)
