"""
Configuración de la aplicación
"""
import os
from dotenv import load_dotenv
from typing import Any

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración global de la aplicación"""
    
    # API Keys
    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
    FAOSTAT_API_KEY = os.getenv('FAOSTAT_API_KEY')
    APIFARMER_KEY = os.getenv('APIFARMER_KEY')
    COMMODITIES_API_KEY = os.getenv('COMMODITIES_API_KEY')
    
    # Firebase
    FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')
    
    # Cache settings
    CACHE_DURATION = 24 * 60 * 60  # 24 horas
    
    @classmethod
    def get_all(cls) -> dict[str, Any]:
        """Retorna todas las configuraciones como diccionario"""
        return {
            'WHATSAPP_ACCESS_TOKEN': cls.WHATSAPP_ACCESS_TOKEN,
            'WHATSAPP_PHONE_NUMBER_ID': cls.WHATSAPP_PHONE_NUMBER_ID,
            'WHATSAPP_VERIFY_TOKEN': cls.WHATSAPP_VERIFY_TOKEN,
            'FAOSTAT_API_KEY': cls.FAOSTAT_API_KEY,
            'APIFARMER_KEY': cls.APIFARMER_KEY,
            'COMMODITIES_API_KEY': cls.COMMODITIES_API_KEY,
            'FIREBASE_CREDENTIALS': cls.FIREBASE_CREDENTIALS,
            'CACHE_DURATION': cls.CACHE_DURATION
        }
