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
    ENV: str = Field(default="development", description="Entorno de ejecución")
    DEBUG: bool = Field(default=False, description="Modo debug")
    
    # WhatsApp API
    WHATSAPP_API_URL: str = Field(
        default="https://graph.facebook.com/v17.0",
        description="URL base de la API de WhatsApp"
    )
    WHATSAPP_TOKEN: str = Field(
        default="",
        description="Token de acceso para la API de WhatsApp"
    )
    WHATSAPP_PHONE_NUMBER_ID: str = Field(
        default="",
        description="ID del número de teléfono de WhatsApp"
    )
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = Field(
        default="",
        description="Token de verificación para el webhook de WhatsApp"
    )
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = Field(
        default=str(BASE_DIR / "firebase-credentials.json"),
        description="Ruta al archivo de credenciales de Firebase"
    )
    
    # MAGA API
    MAGA_BASE_URL: str = Field(
        default="https://web.maga.gob.gt",
        description="URL base del sitio web del MAGA"
    )
    
    # Límites y timeouts
    REQUEST_TIMEOUT: int = Field(
        default=30,
        description="Timeout para requests HTTP en segundos"
    )
    CACHE_TTL: int = Field(
        default=300,
        description="Tiempo de vida del caché en segundos"
    )
    MAX_RETRIES: int = Field(
        default=3,
        description="Número máximo de reintentos para operaciones fallidas"
    )
    
    @validator('ENV')
    def validate_env(cls, v: str) -> str:
        """Valida el entorno"""
        if v not in ['development', 'staging', 'production']:
            raise ValueError("ENV debe ser 'development', 'staging' o 'production'")
        return v
    
    @property
    def FIREBASE_CREDENTIALS(self) -> Dict[str, Any]:
        """
        Lee las credenciales de Firebase desde el archivo o variables de entorno
        
        Returns:
            Dict[str, Any]: Credenciales de Firebase
        """
        try:
            # En producción, usar variables de entorno
            if self.ENV == "production":
                creds = {
                    "type": "service_account",
                    "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
                    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
                    "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", ""),
                    "universe_domain": "googleapis.com"
                }
                
                # Validar credenciales
                required_fields = [
                    "project_id", "private_key_id", "private_key",
                    "client_email", "client_id", "client_x509_cert_url"
                ]
                
                missing_fields = [
                    field for field in required_fields
                    if not creds.get(field)
                ]
                
                if missing_fields:
                    raise ValueError(
                        f"Faltan las siguientes credenciales de Firebase: {', '.join(missing_fields)}"
                    )
                
                return creds
                
            # En desarrollo, leer del archivo
            creds_path = Path(self.FIREBASE_CREDENTIALS_PATH)
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"No se encontró el archivo de credenciales en {creds_path}"
                )
                
            with open(creds_path) as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error cargando credenciales de Firebase: {str(e)}")
            raise
    
    @property
    def IS_PRODUCTION(self) -> bool:
        """Indica si el entorno es producción"""
        return self.ENV == "production"
    
    @property
    def IS_DEVELOPMENT(self) -> bool:
        """Indica si el entorno es desarrollo"""
        return self.ENV == "development"
    
    class Config:
        """Configuración del modelo"""
        env_file = ".env"
        case_sensitive = True

# Instancia global de configuración
try:
    settings = Settings()
    logger.info(f"Configuración cargada para entorno: {settings.ENV}")
except Exception as e:
    logger.error(f"Error cargando configuración: {str(e)}")
    raise
