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
import httpx
from app.utils.constants import ConversationState, MESSAGES
from app.services.whatsapp_service import WhatsAppService
from app.database.firebase import firebase_manager
from app.external_apis.maga import maga_api
from app.analysis.scoring import scoring_service
from app.config import settings

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

def verify_webhook_signature(request: Request) -> bool:
    """
    Verifica la firma del webhook de WhatsApp
    
    Args:
        request: Request de FastAPI
        
    Returns:
        bool: True si la firma es válida
    """
    try:
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not signature or not signature.startswith('sha256='):
            return False
            
        # Obtener firma
        expected_signature = signature.split('sha256=')[1]
        
        # Calcular firma
        secret = settings.WHATSAPP_WEBHOOK_SECRET.encode()
        body = await request.body()
        calculated_signature = hmac.new(
            secret,
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Comparar firmas
        return hmac.compare_digest(calculated_signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Error verificando firma: {str(e)}")
        return False

async def process_user_message(from_number: str, message: str) -> None:
    """
    Procesa el mensaje del usuario y actualiza el estado de la conversación
    """
    try:
        # Obtener estado actual
        conversation_data = await firebase_manager.get_conversation_state(from_number)
        current_state = conversation_data.get('state', ConversationState.INITIAL.value)
        user_data = conversation_data.get('data', {})
        
        # Si el mensaje es "reiniciar", volver al estado inicial
        if message.lower() == "reiniciar":
            await firebase_manager.reset_user_state(from_number)
            await whatsapp.send_message(from_number, MESSAGES['welcome'])
            return
            
        # Procesar mensaje según el estado actual
        if current_state == ConversationState.INITIAL.value:
            # Mensaje de bienvenida
            user_data['name'] = message
            new_state = ConversationState.ASKING_CROP.value
            await whatsapp.send_message(from_number, MESSAGES['ask_crop'])
            
        elif current_state == ConversationState.ASKING_CROP.value:
            # Guardar cultivo y obtener precio
            user_data['crop'] = message
            
            try:
                precio_info = await maga_api.get_precio_cultivo(message)
                if precio_info:
                    user_data['precio_info'] = precio_info
                    logger.info(f"Precio encontrado para {message}")
            except Exception as e:
                logger.error(f"Error obteniendo precios: {str(e)}")
            
            new_state = ConversationState.ASKING_AREA.value
            await whatsapp.send_message(from_number, MESSAGES['ask_area'])
            
        elif current_state == ConversationState.ASKING_AREA.value:
            # Guardar área
            try:
                area = float(message.replace('ha', '').strip())
                user_data['area'] = area
                new_state = ConversationState.ASKING_COMMERCIALIZATION.value
                await whatsapp.send_message(from_number, MESSAGES['ask_commercialization'])
            except ValueError:
                await whatsapp.send_message(from_number, MESSAGES['invalid_area'])
                return
                
        elif current_state == ConversationState.ASKING_COMMERCIALIZATION.value:
            # Guardar método de comercialización
            user_data['commercialization'] = message
            new_state = ConversationState.ASKING_IRRIGATION.value
            await whatsapp.send_message(from_number, MESSAGES['ask_irrigation'])
            
        elif current_state == ConversationState.ASKING_IRRIGATION.value:
            # Guardar sistema de riego
            user_data['irrigation'] = message
            new_state = ConversationState.ASKING_LOCATION.value
            await whatsapp.send_message(from_number, MESSAGES['ask_location'])
            
        elif current_state == ConversationState.ASKING_LOCATION.value:
            # Guardar ubicación y generar análisis
            user_data['location'] = message
            new_state = ConversationState.ANALYSIS.value
            
            # Generar y guardar análisis
            analysis = await scoring_service.generate_analysis(user_data)
            await firebase_manager.store_analysis(from_number, analysis)
            
            # Enviar resultados
            await whatsapp.send_message(from_number, MESSAGES['analysis_ready'])
            
        else:
            # Estado no reconocido, reiniciar
            await firebase_manager.reset_user_state(from_number)
            await whatsapp.send_message(from_number, MESSAGES['error_restart'])
            return
            
        # Actualizar estado en Firebase
        await firebase_manager.update_user_state(from_number, {
            'state': new_state,
            'data': user_data
        })
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        await whatsapp.send_message(from_number, MESSAGES['error'])

@app.get("/")
async def root():
    """
    Ruta raíz que muestra información básica de la API
    """
    return {
        "name": "FinGro API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENV,
        "docs_url": "/docs"
    }

@app.post("/webhook/whatsapp")
async def webhook(request: Request):
    """
    Endpoint para recibir webhooks de WhatsApp
    """
    try:
        # Verificar firma
        if not settings.DEBUG and not await verify_webhook_signature(request):
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Obtener y parsear body
        body = await request.body()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Procesar mensajes
        messages_processed = 0
        
        if "entry" in data and len(data["entry"]) > 0:
            for entry in data["entry"]:
                if "changes" in entry and len(entry["changes"]) > 0:
                    for change in entry["changes"]:
                        if "value" in change and "messages" in change["value"]:
                            for message in change["value"]["messages"]:
                                if message["type"] == "text":
                                    from_number = message["from"]
                                    message_text = message["text"]["body"]
                                    logger.info(f"Mensaje recibido de: {from_number}")
                                    await process_user_message(from_number, message_text)
                                    messages_processed += 1
        
        logger.info(f"Procesados {messages_processed} mensajes exitosamente")
        return JSONResponse(content={"status": "success"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Internal server error"}
        )

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """
    Endpoint para verificar webhook de WhatsApp
    """
    try:
        verify_token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        if not verify_token or not challenge:
            raise HTTPException(status_code=400, detail="Missing parameters")
        
        if verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Invalid verify token")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Internal server error"}
        )

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado del servicio
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Obtener puerto de Render o usar 8000 por defecto
    port = int(os.getenv("PORT", "8000"))
    
    # Iniciar servidor
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )
