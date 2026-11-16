
from fastapi import FastAPI

from app.api.routes import router as incident_router


app = FastAPI(
    title="Cloud Chaos Theatre API",
    description=(
        "A deterministic cloud infrastructure failure "
        "simulation and incident analysis platform."
    ),
    version="0.1.0",
)

app.include_router(incident_router, prefix="/api", tags=["Incidents"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}
