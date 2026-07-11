import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit import router as audit_router
from app.config import settings
from app.services.croo_provider import CrooProvider


logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name, version=settings.app_version)
croo_provider = CrooProvider()
_croo_start_task: asyncio.Task[None] | None = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router)


def _log_croo_start_result(task: asyncio.Task[None]) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        return
    except Exception:
        logger.exception("CROO provider background startup failed")


@app.on_event("startup")
async def start_croo_provider() -> None:
    global _croo_start_task

    if not croo_provider.is_configured:
        logger.info("CROO provider is not configured; skipping background startup")
        return

    _croo_start_task = asyncio.create_task(croo_provider.start())
    _croo_start_task.add_done_callback(_log_croo_start_result)


@app.on_event("shutdown")
async def stop_croo_provider() -> None:
    global _croo_start_task

    await croo_provider.stop()
    if _croo_start_task is not None and not _croo_start_task.done():
        _croo_start_task.cancel()
    _croo_start_task = None


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "running"}


@app.get("/health")
def health() -> dict[str, bool | str]:
    return {
        "status": "ok",
        "croo_provider_configured": croo_provider.is_configured,
        "croo_provider_started": croo_provider._started,
    }