import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.doc_type import router as doc_type_router
from src.api.routes.export import router as export_router
from src.api.routes.extract import router as extract_router
from src.api.routes.health import router as health_router
from src.api.routes.jobs import router as jobs_router
from src.api.routes.patch import router as patch_router
from src.core.job_store import job_store

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes


async def _cleanup_loop() -> None:
    """Periodically remove expired jobs from the store."""
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            removed = await job_store.cleanup_expired_jobs()
            if removed > 0:
                logger.info("Cleaned up %d expired job(s)", removed)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error during job cleanup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="DocExtract", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(extract_router)
app.include_router(jobs_router)
app.include_router(doc_type_router)
app.include_router(export_router)
app.include_router(patch_router)

if __name__ == "__main__":
    import uvicorn

    from src.core.config import settings

    uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
