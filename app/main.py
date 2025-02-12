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
        actual_signature = signature.replace('sha256=', '')
        return hmac.compare_digest(actual_signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Error verificando firma: {str(e)}")
        return False

@app.post("/webhook")
async def webhook(request: Request):
    """Endpoint para recibir webhooks de WhatsApp"""
    try:
        # Verificar firma
        if not settings.DEBUG and not await verify_webhook_signature(request):
            logger.warning("Firma inválida en webhook")
            return JSONResponse(status_code=401, content={"error": "Firma inválida"})
            
        # Procesar webhook
        body = await request.json()
        
        # Validar estructura del webhook
        if 'entry' not in body or not body['entry']:
            logger.warning("Webhook sin entradas")
            return JSONResponse(status_code=400, content={"error": "Webhook inválido"})
            
        # Procesar cada mensaje
        for entry in body['entry']:
            for change in entry.get('changes', []):
                if change.get('value', {}).get('messages'):
                    for message in change['value']['messages']:
                        # Obtener número y mensaje
                        from_number = message['from']
                        text = message.get('text', {}).get('body', '')
                        
                        # Procesar mensaje
                        await conversation_flow.handle_message(from_number, text)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor"}
        )

@app.get("/")
async def root():
    """Ruta raíz que muestra información básica de la API"""
    return {
        "name": "FinGro API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENV
    }

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Endpoint para verificar webhook de WhatsApp"""
    try:
        # Obtener parámetros
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')
        
        # Validar modo y token
        if mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            if not challenge:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Challenge no proporcionado"}
                )
            return Response(content=challenge, media_type="text/plain")
        
        return JSONResponse(status_code=403, content={"error": "Token inválido"})
        
    except Exception as e:
        logger.error(f"Error en verificación de webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor"}
        )

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Obtener puerto de Render o usar 8000 por defecto
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )
