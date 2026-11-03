from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DB_PATH = BASE_DIR / "jalrakshak.db"

class Settings(BaseModel):
    APP_NAME: str = "JalRakshak NCR — Flood Management Platform"
    API_PREFIX: str = "/api"
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"
    GURUGRAM_LAT: float = 28.4595
    GURUGRAM_LNG: float = 77.0266
    CORS_ORIGINS: list[str] = ["*"]

settings = Settings()
