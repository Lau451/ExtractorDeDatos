from fastapi import FastAPI

from src.api.routes.doc_type import router as doc_type_router
from src.api.routes.extract import router as extract_router
from src.api.routes.health import router as health_router
from src.api.routes.jobs import router as jobs_router

app = FastAPI(title="DocExtract", version="0.1.0")
app.include_router(health_router)
app.include_router(extract_router)
app.include_router(jobs_router)
app.include_router(doc_type_router)

if __name__ == "__main__":
    import uvicorn

    from src.core.config import settings

    uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
