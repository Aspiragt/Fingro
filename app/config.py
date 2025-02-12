"""
Configuración de la aplicación
"""
import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno
load_dotenv(BASE_DIR / ".env")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class Settings(BaseModel):
    """Configuración de la aplicación"""
    
    # Entorno
    ENV: str = Field(
        default=os.getenv("ENV", "development"),
        description="Entorno de ejecución"
    )
    DEBUG: bool = Field(
        default=os.getenv("DEBUG", "false").lower() == "true",
        description="Modo debug"
    )
    LOG_LEVEL: str = Field(
        default=os.getenv("LOG_LEVEL", "INFO").upper(),
        description="Nivel de logging"
    )
    
    # WhatsApp API
    WHATSAPP_API_URL: str = Field(
        default="https://graph.facebook.com/v17.0",
        description="URL base de la API de WhatsApp"
    )
    WHATSAPP_TOKEN: str = Field(
        default=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
        description="Token de acceso para la API de WhatsApp"
    )
    WHATSAPP_PHONE_ID: str = Field(
        default=os.getenv("WHATSAPP_PHONE_ID", ""),
        description="ID del número de WhatsApp"
    )
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = Field(
        default=os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""),
        description="Token para verificar webhooks de WhatsApp"
    )
    WHATSAPP_WEBHOOK_SECRET: str = Field(
        default=os.getenv("WHATSAPP_WEBHOOK_SECRET", ""),
        description="Secreto para verificar firmas de webhooks"
    )
    
    # Firebase
    FIREBASE_CREDENTIALS: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(os.getenv("FIREBASE_CREDENTIALS_JSON", "{}")),
        description="Credenciales de Firebase en formato JSON"
    )
    FIREBASE_CACHE_TTL: int = Field(
        default=int(os.getenv("FIREBASE_CACHE_TTL", "300")),
        description="Tiempo de vida del caché en segundos"
    )
    FIREBASE_CACHE_MAXSIZE: int = Field(
        default=int(os.getenv("FIREBASE_CACHE_MAXSIZE", "1000")),
        description="Tamaño máximo del caché"
    )
    
    # MAGA API
    MAGA_BASE_URL: str = Field(
        default="https://maga.gt/api/v1",
        description="URL base de la API de MAGA"
    )
    
    # Seguridad
    CORS_ORIGINS: list = Field(
        default=json.loads(os.getenv("CORS_ORIGINS", '["*"]')),
        description="Orígenes permitidos para CORS"
    )
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        description="Límite de requests por minuto"
    )
    
    # Validaciones
    @validator("WHATSAPP_TOKEN")
    def validate_whatsapp_token(cls, v: str) -> str:
        """Valida que el token de WhatsApp esté presente"""
        if not v:
            raise ValueError("WHATSAPP_TOKEN es requerido")
        return v
    
    @validator("WHATSAPP_PHONE_ID")
    def validate_whatsapp_phone_id(cls, v: str) -> str:
        """Valida que el phone_id de WhatsApp esté presente"""
        if not v:
            raise ValueError("WHATSAPP_PHONE_ID es requerido")
        if not re.match(r'^\d{4,}$', v):
            raise ValueError("WHATSAPP_PHONE_ID debe ser un número entero de al menos 4 dígitos")
        return v
    
    @validator("FIREBASE_CREDENTIALS")
    def validate_firebase_credentials(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Valida que las credenciales de Firebase existan"""
        if not v:
            raise ValueError("FIREBASE_CREDENTIALS es requerido")
        return v
    
    @validator("WHATSAPP_WEBHOOK_SECRET")
    def validate_webhook_secret(cls, v: str, values: Dict[str, Any]) -> str:
        """Valida que el secreto del webhook esté presente en producción"""
        if values.get("ENV") == "production" and not v:
            raise ValueError("WHATSAPP_WEBHOOK_SECRET es requerido en producción")
        return v
    
    class Config:
        """Configuración del modelo"""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instancia global de configuración
try:
    settings = Settings()
    logger.info(f"Configuración cargada para entorno: {settings.ENV}")
except Exception as e:
    logger.error(f"Error cargando configuración: {str(e)}")
    raise
