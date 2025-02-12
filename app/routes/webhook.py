"""
Rutas para el webhook de WhatsApp
"""
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from typing import Any
from app.services.whatsapp_service import WhatsAppService
from app.database.firebase import firebase_manager
from app.chat.conversation_flow import conversation_flow
import logging
from datetime import datetime
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/whatsapp")
async def verify_webhook(request: Request):
    """Verify webhook for WhatsApp API"""
    try:
        # Obtener parámetros
        params = dict(request.query_params)
        verify_token = params.get("hub.verify_token")
        mode = params.get("hub.mode")
        challenge = params.get("hub.challenge")

        logger.info(f"Webhook verification request: mode={mode}, token={verify_token}, challenge={challenge}")

        # Verificar token
        if mode == "subscribe" and verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            if challenge:
                logger.info("Webhook verified successfully")
                return Response(content=challenge, media_type="text/plain")
            else:
                logger.warning("Missing challenge parameter")
                raise HTTPException(status_code=400, detail="Missing challenge parameter")
        else:
            logger.warning("Invalid verification request")
            raise HTTPException(status_code=403, detail="Invalid verification request")

    except Exception as e:
        logger.error(f"Error verifying webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whatsapp")
async def receive_message(request: Request, whatsapp: WhatsAppService = Depends()):
    """Handle incoming WhatsApp messages"""
    try:
        # Obtener body del request
        body = await request.json()
        logger.info(f"Received webhook: {body}")
        
        # Extraer datos del mensaje
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            logger.warning("No messages in webhook")
            return {"status": "success"}
            
        # Procesar cada mensaje
        for message in messages:
            try:
                # Extraer texto del mensaje
                text = message.get("text", {}).get("body", "").strip()
                if not text:
                    continue
                    
                logger.info(f"Processing message: {text}")
                
                # Obtener número de teléfono
                metadata = value.get("metadata", {})
                phone = metadata.get("phone_number_id")
                
                if not phone:
                    logger.warning("No phone number in message")
                    continue
                
                # Procesar mensaje con el flujo de conversación
                response = await conversation_flow.process_message(text, phone)
                
                if response:
                    # Enviar respuesta
                    await whatsapp.send_message(phone, response)
                    logger.info(f"Response sent: {response[:50]}...")
                    
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                continue
                
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Firebase connection
        db = firebase_manager.get_firebase_db()
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
