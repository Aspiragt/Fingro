"""
Configuración de la aplicación
"""
import os
from typing import Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings(BaseModel):
    """Configuración de la aplicación"""
    
    # WhatsApp API
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v17.0"
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    
    # Firebase
    FIREBASE_CREDENTIALS: Dict[str, Any] = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
        "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", "")
    }
    
    # MAGA API
    MAGA_BASE_URL: str = "https://precios.maga.gob.gt"
    MAGA_CACHE_TTL: int = 21600  # 6 horas en segundos
    
    # Configuración de la aplicación
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Límites y configuraciones
    MAX_CACHE_SIZE: int = 1000
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    class Config:
        """Configuración de Pydantic"""
        env_file = ".env"
        case_sensitive = True

# Instancia global de configuración
settings = Settings()
