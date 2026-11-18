
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as incident_router


app = FastAPI(
    title="Cloud Chaos Theatre API",
    description=(
        "A deterministic cloud infrastructure failure "
        "simulation and incident analysis platform."
    ),
    version="0.1.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

app.include_router(incident_router, prefix="/api", tags=["Incidents"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}

