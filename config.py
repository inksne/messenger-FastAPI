from dotenv import load_dotenv
import os
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")


class AuthJWT(BaseModel):
    private_key_path: Path = Path("certs") / "jwt-private.pem"
    public_key_path: Path = Path("certs") / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 5
    refresh_token_expire_days: int = 14


class Settings(BaseSettings):
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()

class DBSettings(BaseSettings):
    db_url: str = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    db_echo: bool = False

db_settings = DBSettings()