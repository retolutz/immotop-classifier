"""
Immotop Invoice Classifier - FastAPI Backend

Ein intelligenter Rechnungsklassifikator für die Schweizer Immobilienbuchhaltung.
Verwendet Claude (Anthropic) für semantische Analyse und automatische Kontozuordnung.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router

app = FastAPI(
    title=settings.app_name,
    description="Automatische Rechnungsklassifikation für Immotop2",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS für Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "mock_mode": settings.immotop_mock_mode,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
