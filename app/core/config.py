"""Configuration for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

env_path = Path(".") / ".env"

load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Settings for the application."""

    # Database

    ENVIRONMENT: str = os.environ.get('ENVIRONMENT')


    if ENVIRONMENT == 'dev':
        DB_USER: str = os.environ.get('DEV_DB_USER')
        DB_PASSWORD: str = os.environ.get('DEV_DB_PASSWORD')
        DB_HOST: str = os.environ.get('DEV_DB_HOST')
        DB_PORT: str = os.environ.get('DEV_DB_PORT')
        DB_NAME: str = os.environ.get('DEV_DB_NAME')
        DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        DB_USER: str = os.environ.get('DB_USER')
        DB_PASSWORD: str = os.environ.get('DB_PASSWORD')
        DB_HOST: str = os.environ.get('DB_HOST')
        DB_PORT: str = os.environ.get('DB_PORT')
        DB_NAME: str = os.environ.get('DB_NAME')
        MYSQL_ATTR_SSL_CA: str = os.environ.get('MYSQL_ATTR_SSL_CA')
        DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?ssl_ca={MYSQL_ATTR_SSL_CA}"



# or from config import get_settings -> var = get_settings()
def get_settings() -> Settings:
    """Get the settings to use within application."""
    return Settings()
