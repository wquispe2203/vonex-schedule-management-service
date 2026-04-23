import os
from enum import Enum

class MigrationPolicy(str, Enum):
    WARN = "warn"
    SOFT_BLOCK = "soft-block"
    HARD_BLOCK = "hard-block"

class Settings:
    # Por defecto 'warn' para progresividad segura
    UUID_MIGRATION_POLICY: MigrationPolicy = os.getenv("UUID_MIGRATION_POLICY", MigrationPolicy.WARN)
    
    # Detección de entorno
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # MDM Matching Threshold (0-100)
    FUZZY_THRESHOLD: int = int(os.getenv("FUZZY_THRESHOLD", 90))
    
    # Configuración de CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        origin.strip() 
        for origin in os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080").split(",")
        if origin.strip()
    ]
    
    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT.lower() == "staging"

settings = Settings()
