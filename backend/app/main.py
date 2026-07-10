from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit import router as audit_router
from app.api.croo import router as croo_router
from app.config import settings
from app.services.croo_service import croo_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await croo_service.start()
    try:
        yield
    finally:
        await croo_service.stop()


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router)
app.include_router(croo_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "running"}
