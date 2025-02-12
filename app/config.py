"""
Configuración de la aplicación
"""
import os
import json
import logging
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
    DEBUG: bool = Field(
        default=os.getenv("DEBUG", "False").lower() == "true",
        description="Modo debug"
    )
    LOG_LEVEL: str = Field(
        default=os.getenv("LOG_LEVEL", "INFO"),
        description="Nivel de logging"
    )
    
    # WhatsApp API
    WHATSAPP_ACCESS_TOKEN: str = Field(
        default=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
        description="Token de acceso para la API de WhatsApp"
    )
    WHATSAPP_PHONE_NUMBER_ID: str = Field(
        default=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
        description="ID del número de teléfono de WhatsApp"
    )
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = Field(
        default=os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""),
        description="Token para verificar webhook de WhatsApp"
    )
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = Field(
        default=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
        description="Ruta al archivo de credenciales de Firebase"
    )
    
    # Validaciones
    @validator("WHATSAPP_ACCESS_TOKEN")
    def validate_whatsapp_token(cls, v: str) -> str:
        """Valida que el token de WhatsApp esté presente"""
        if not v:
            raise ValueError("WHATSAPP_ACCESS_TOKEN es requerido")
        return v
    
    @validator("WHATSAPP_PHONE_NUMBER_ID")
    def validate_whatsapp_phone_id(cls, v: str) -> str:
        """Valida que el phone_id de WhatsApp esté presente"""
        if not v:
            raise ValueError("WHATSAPP_PHONE_NUMBER_ID es requerido")
        return v
    
    @validator("FIREBASE_CREDENTIALS_PATH")
    def validate_firebase_credentials(cls, v: str) -> str:
        """Valida que el archivo de credenciales de Firebase exista"""
        if not v:
            raise ValueError("FIREBASE_CREDENTIALS_PATH es requerido")
        if not os.path.exists(v):
            raise ValueError(f"El archivo de credenciales no existe: {v}")
        try:
            with open(v) as f:
                json.load(f)  # Validar que es JSON válido
        except json.JSONDecodeError:
            raise ValueError("El archivo de credenciales debe ser un JSON válido")
        except Exception as e:
            raise ValueError(f"Error leyendo archivo de credenciales: {str(e)}")
        return v

# Instancia global de configuración
try:
    settings = Settings()
    logger.info(f"Configuración cargada en puerto: {settings.PORT}")
except Exception as e:
    logger.error(f"Error cargando configuración: {str(e)}")
    raise
