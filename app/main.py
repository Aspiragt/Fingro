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

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

async def verify_webhook_signature(request: Request) -> bool:
    """
    Verifica la firma del webhook de WhatsApp
    """
    try:
        signature = request.headers.get('x-hub-signature-256', '')
        if not signature:
            logger.warning("No se encontró firma en el webhook")
            return False
            
        # Obtener el cuerpo del request
        body = await request.body()
        
        # Calcular firma esperada
        expected_signature = hmac.new(
            settings.WHATSAPP_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Comparar firmas
        return hmac.compare_digest(
            f"sha256={expected_signature}",
            signature
        )
        
    except Exception as e:
        logger.error(f"Error verificando firma: {str(e)}")
        return False

@app.post("/webhook/whatsapp")
async def webhook(request: Request):
    """
    Endpoint para recibir webhooks de WhatsApp
    """
    try:
        # Verificar firma
        if not settings.DISABLE_WEBHOOK_SIGNATURE:
            if not await verify_webhook_signature(request):
                raise HTTPException(status_code=401, detail="Firma inválida")
        
        # Obtener datos del webhook
        data = await request.json()
        logger.debug(f"Webhook recibido: {json.dumps(data, indent=2)}")
        
        # Procesar solo si es mensaje de WhatsApp
        if "entry" in data and len(data["entry"]) > 0:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    if change.get("value", {}).get("messages"):
                        for message in change["value"]["messages"]:
                            # Obtener número y mensaje
                            phone = message["from"]
                            text = message.get("text", {}).get("body", "")
                            
                            # Procesar mensaje
                            await conversation_flow.handle_message(phone, text)
        
        return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/")
def root():
    """Ruta raíz que muestra información básica de la API"""
    return {
        "name": "FinGro API",
        "version": "1.0.0",
        "status": "running",
        "env": settings.ENV,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Endpoint para verificar webhook de WhatsApp
    
    WhatsApp envía un desafío que debemos responder para verificar
    que somos dueños del endpoint
    """
    try:
        # Obtener parámetros
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        # Verificar modo y token
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            if challenge:
                return Response(content=challenge)
            return Response(status_code=200)
            
        # Token inválido
        raise HTTPException(status_code=403, detail="Token inválido")
        
    except Exception as e:
        logger.error(f"Error verificando webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Endpoint para verificar el estado del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "env": settings.ENV
    }

if __name__ == "__main__":
    import uvicorn
    
    # Obtener puerto de Render o usar 8000 por defecto
    port = int(os.environ.get("PORT", 8000))
    
    # Iniciar servidor
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENV == "development"
    )
