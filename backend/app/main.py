
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.services.mqtt_service import start_mqtt, stop_mqtt

from app.db.session import engine
from app import models

from app.api.categories import router as categories_router
from app.api.products import router as products_router
from app.api.batches import router as batches_router
from app.api.shelves import router as shelves_router
from app.api.inventory import router as inventory_router
from app.api.alerts import router as alerts_router
from app.api.dashboard import router as dashboard_router


app = FastAPI(
    title="SMARTSHELF API",
    description="Smart inventory and expiration monitoring system",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    start_mqtt()


@app.on_event("shutdown")
def shutdown_event():
    stop_mqtt()

app.include_router(categories_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(batches_router, prefix="/api")
app.include_router(shelves_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Welcome to SMARTSHELF API",
        "status": "running",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        )
