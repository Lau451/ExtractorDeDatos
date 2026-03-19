from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    docling_timeout_seconds: float = 60.0
    docling_artifacts_path: str = ""
    ocr_min_chars: int = 50
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
