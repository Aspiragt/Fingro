"""
Rutas para el webhook de WhatsApp
"""
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from typing import Any
from app.services.whatsapp_service import WhatsAppService
from app.database.firebase import firebase_manager
from app.chat.conversation_flow import conversation_flow
from app.config.settings import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/whatsapp")
async def verify_webhook(request: Request):
    """Verify webhook for WhatsApp API"""
    try:
        params = dict(request.query_params)
        verify_token = params.get("hub.verify_token")
        mode = params.get("hub.mode")
        challenge = params.get("hub.challenge")

        if mode and verify_token:
            if mode == "subscribe":
                logger.info("Webhook verified successfully")
                return Response(content=challenge, media_type="text/plain")
            else:
                raise HTTPException(status_code=403, detail="Invalid mode")
        else:
            raise HTTPException(status_code=403, detail="Missing parameters")

    except Exception as e:
        logger.error(f"Error verifying webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whatsapp")
async def receive_message(request: Request, whatsapp: WhatsAppService = Depends()):
    """Handle incoming WhatsApp messages"""
    try:
        body = await request.json()
        
        # Log incoming webhook
        logger.info(f"Received webhook body: {body}")
        
        # Extract message data
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        logger.info(f"Extracted messages: {messages}")
        
        if not messages:
            logger.info("No messages found in webhook")
            return {"status": "no_messages"}
            
        # Process each message
        for message in messages:
            from_number = message.get("from")
            message_type = message.get("type")
            
            logger.info(f"Processing message - From: {from_number}, Type: {message_type}")
            
            if not from_number or not message_type:
                logger.warning(f"Invalid message format - from: {from_number}, type: {message_type}")
                continue
                
            if message_type == "text":
                text = message.get("text", {}).get("body", "")
                logger.info(f"Processing text message: {text}")
                # Procesar el mensaje usando conversation_flow
                response = await conversation_flow.handle_message(from_number, text)
                logger.info(f"Generated response: {response}")
                # Enviar respuesta al usuario
                await whatsapp.send_message(from_number, response)
                logger.info(f"Response sent to {from_number}")
            
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
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
