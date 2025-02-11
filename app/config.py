"""
Configuración de la aplicación
"""
import os
import json
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    """Configuración de la aplicación"""
    
    # Entorno
    ENV: str = os.getenv("ENV", "development")
    
    # WhatsApp API
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v17.0"
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", str(BASE_DIR / "firebase-credentials.json"))
    
    @property
    def FIREBASE_CREDENTIALS(self) -> Dict[str, Any]:
        """Lee las credenciales de Firebase desde el archivo o variables de entorno"""
        try:
            # En producción, usar variables de entorno
            if self.ENV == "production":
                return {
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
            
            # En desarrollo, usar archivo
            creds_path = Path(self.FIREBASE_CREDENTIALS_PATH)
            if not creds_path.is_absolute():
                creds_path = BASE_DIR / creds_path
            
            with open(creds_path) as f:
                return json.load(f)
                
        except Exception as e:
            raise ValueError(f"Error leyendo credenciales de Firebase: {str(e)}")
    
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
