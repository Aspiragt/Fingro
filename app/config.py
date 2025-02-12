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
    PORT: int = Field(
        default=int(os.getenv("PORT", "8000")),
        description="Puerto para el servidor"
    )
    
    # WhatsApp API
    WHATSAPP_TOKEN: str = Field(
        default=os.getenv("WHATSAPP_TOKEN", ""),
        description="Token de acceso para la API de WhatsApp"
    )
    WHATSAPP_PHONE_ID: str = Field(
        default=os.getenv("WHATSAPP_PHONE_ID", ""),
        description="ID del número de teléfono de WhatsApp"
    )
    WHATSAPP_VERIFY_TOKEN: str = Field(
        default=os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
        description="Token para verificar webhook de WhatsApp"
    )
    
    # Firebase
    FIREBASE_CREDENTIALS: str = Field(
        default=os.getenv("FIREBASE_CREDENTIALS", ""),
        description="Credenciales de Firebase en formato JSON"
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
        return v
    
    @validator("FIREBASE_CREDENTIALS")
    def validate_firebase_credentials(cls, v: str) -> str:
        """Valida que las credenciales de Firebase existan"""
        if not v:
            raise ValueError("FIREBASE_CREDENTIALS es requerido")
        try:
            json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("FIREBASE_CREDENTIALS debe ser un JSON válido")
        return v
    
    class Config:
        """Configuración del modelo"""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instancia global de configuración
try:
    settings = Settings()
    logger.info(f"Configuración cargada en puerto: {settings.PORT}")
except Exception as e:
    logger.error(f"Error cargando configuración: {str(e)}")
    raise
