from fastapi import FastAPI

from src.api.routes.health import router as health_router

app = FastAPI(title="DocExtract", version="0.1.0")
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    from src.core.config import settings

    uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
