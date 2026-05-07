import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    # --- DATABASE ---
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    TEST_DATABASE_URL: str = Field(None, env="TEST_DATABASE_URL")
    
    # --- ENVIRONMENT ---
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    TESTING: bool = Field(False, env="TESTING")
    
    # --- POLICIES ---
    UUID_MIGRATION_POLICY: str = Field("warn", env="UUID_MIGRATION_POLICY")
    FUZZY_THRESHOLD: int = Field(90, env="FUZZY_THRESHOLD")
    
    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5500", "http://127.0.0.1:5500"],
        env="CORS_ORIGINS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def database_url(self) -> str:
        if self.TESTING:
            if not self.TEST_DATABASE_URL:
                raise ValueError("TESTING is True but TEST_DATABASE_URL is not set.")
            if self.TEST_DATABASE_URL == self.DATABASE_URL:
                raise ValueError("CRITICAL: TEST_DATABASE_URL is identical to DATABASE_URL while TESTING=True. Risk of production data loss!")
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL

    def log_active_config(self):
        """Logs the current critical settings without exposing credentials."""
        import logging
        logger = logging.getLogger("app.config")
        
        db_type = "TEST" if self.TESTING else "PRODUCTION"
        db_host = self.database_url.split("@")[-1].split("/")[0] if "@" in self.database_url else "unknown"
        
        logger.info(f"--- ACTIVE CONFIGURATION ---")
        logger.info(f"Environment: {self.ENVIRONMENT}")
        logger.info(f"Testing Mode: {self.TESTING}")
        logger.info(f"Database Type: {db_type}")
        logger.info(f"Database Host: {db_host}")
        logger.info(f"----------------------------")

settings = Settings()
# Log config on module load
settings.log_active_config()
