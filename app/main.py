"""
FastAPI app principal
"""
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import json
import logging
import os
import hmac
import hashlib
from datetime import datetime

from app.config import settings
from app.services.whatsapp_service import WhatsAppService
from app.chat.conversation_flow import conversation_flow
from app.database.firebase import firebase_manager
from app.routes.webhook import router as webhook_router

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Forzar la configuración
)

# Configurar loggers específicos
for logger_name in ['app.routes.webhook', 'app.chat.conversation_flow', 'app.services.whatsapp_service']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info(f"Iniciando FinGro Bot en modo: {settings.ENV}")

# Crear la app FastAPI
app = FastAPI(
    title="FinGro API",
    description="API para el chatbot de FinGro",
    version="1.0.0"
)

# Instanciar servicios
whatsapp = WhatsAppService()

# Incluir routers
app.include_router(webhook_router, tags=["webhook"])

@app.get("/")
async def root():
    """Ruta raíz que muestra información básica de la API"""
    return {
        "name": "FinGro API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado del servicio"""
    try:
        # Verificar conexión a Firebase
        db = firebase_manager.db
        if not db:
            raise Exception("Firebase connection failed")
            
        return {
            "status": "healthy",
            "firebase": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
