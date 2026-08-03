# meditrack-ai/config.py

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8000))
    API_DEBUG: bool = os.getenv("API_DEBUG", "True").lower() == "true"
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "MediTrack AI - Analyse Tension Artérielle"
    API_DESCRIPTION: str = "API d'intelligence artificielle pour l'analyse des tensions artérielles"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    # Sécurité
    API_KEY: str = os.getenv("API_KEY", "dev-api-key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-key")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
    
    # Performance
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 3600))
    MAX_MEASURES_FOR_ANALYSIS: int = int(os.getenv("MAX_MEASURES_FOR_ANALYSIS", 100))
    
    # Chemins
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/trained_model.pkl")
    REFERENCE_VALUES_PATH: str = os.getenv("REFERENCE_VALUES_PATH", "data/reference_values.json")
    
    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> List[str]:
        """Convertir la chaîne en liste d'origines"""
        return [origin.strip() for origin in v.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instance globale des settings
settings = Settings()