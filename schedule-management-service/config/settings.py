import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List

class Settings(BaseSettings):
    # Base de datos (Obligatoria)
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Entorno
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    TESTING: bool = Field(False, env="TESTING")
    
    # Optional Test DB explicit URL
    TEST_DATABASE_URL: str = Field(None, env="TEST_DATABASE_URL")
    
    # CORS
    CORS_ORIGINS_RAW: str = Field("", env="CORS_ORIGINS")
    
    # Políticas internas (Heredadas del proyecto original)
    UUID_MIGRATION_POLICY: str = Field("warn", env="UUID_MIGRATION_POLICY")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Retorna la URL de base de datos adecuada según el modo (dev o testing)"""
        if self.TESTING:
            if self.TEST_DATABASE_URL:
                return self.TEST_DATABASE_URL
            if "schedule_db" in self.DATABASE_URL:
                # Reemplazo seguro para asegurar aislamiento total en PostgreSQL
                return self.DATABASE_URL.replace("schedule_db", "schedule_test_db")
            return self.DATABASE_URL
        return self.DATABASE_URL

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def cors_origins(self) -> List[str]:
        # Lista explícita de orígenes permitidos (SIN COMODINES)
        allowed = [
            "http://127.0.0.1:5500",
            "http://localhost:5500"
        ]
        
        # Agregar orígenes desde el entorno si existen
        if self.CORS_ORIGINS_RAW:
            from_env = [
                o.strip().rstrip("/") 
                for o in self.CORS_ORIGINS_RAW.split(",") 
                if o.strip() and o.strip() != "*"
            ]
            allowed.extend(from_env)
            
        return list(set(allowed))

# Instancia única de settings
settings = Settings()
