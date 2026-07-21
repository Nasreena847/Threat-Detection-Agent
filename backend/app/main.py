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
        print(f"CROO provider startup task finished; started={croo_provider._started}", flush=True)
    except asyncio.CancelledError:
        return
    except Exception as exc:
        print(f"CROO provider background startup failed: {exc}", flush=True)
        logger.exception("CROO provider background startup failed")


@app.on_event("startup")
async def start_croo_provider() -> None:
    global _croo_start_task

    print(
        "FastAPI startup: "
        f"croo_provider_configured={croo_provider.is_configured} "
        f"api_key_set={bool(croo_provider._api_key)} "
        f"base_url_set={bool(croo_provider._base_url)} "
        f"ws_url_set={bool(croo_provider._ws_url)} "
        f"service_id_set={bool(croo_provider._service_id)}",
        flush=True,
    )

    if not croo_provider.is_configured:
        print("CROO provider startup skipped because required env vars are missing", flush=True)
        logger.info("CROO provider is not configured; skipping background startup")
        return

    print("CROO provider startup scheduled", flush=True)
    _croo_start_task = asyncio.create_task(croo_provider.start())
    _croo_start_task.add_done_callback(_log_croo_start_result)


@app.on_event("shutdown")
async def stop_croo_provider() -> None:
    global _croo_start_task

    print("FastAPI shutdown: stopping CROO provider", flush=True)
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
