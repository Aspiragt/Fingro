"""
FastAPI app principal
"""
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import json
import logging
import os
from datetime import datetime
import httpx
from app.utils.constants import ConversationState, MESSAGES
from app.services.whatsapp_service import WhatsAppService
from app.database.firebase import firebase_manager
from app.external_apis.maga import maga_api
from app.analysis.scoring import scoring_service
from app.config import settings

# Configurar logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="FinGro API")

async def process_user_message(from_number: str, message: str) -> None:
    """
    Procesa el mensaje del usuario y actualiza el estado de la conversación
    """
    try:
        # Obtener estado actual
        conversation_data = firebase_manager.get_conversation_state(from_number)
        current_state = conversation_data.get('state', ConversationState.INITIAL.value)
        user_data = conversation_data.get('data', {})
        
        # Si el mensaje es "reiniciar", volver al estado inicial
        if message.lower() == "reiniciar":
            firebase_manager.reset_user_state(from_number)
            await WhatsAppService.send_message(from_number, MESSAGES['welcome'])
            return
            
        # Procesar mensaje según el estado actual
        if current_state == ConversationState.INITIAL.value:
            # Mensaje de bienvenida
            user_data['name'] = message
            new_state = ConversationState.ASKING_CROP.value
            await WhatsAppService.send_message(from_number, MESSAGES['ask_crop'])
            
        elif current_state == ConversationState.ASKING_CROP.value:
            # Guardar cultivo y obtener precio
            user_data['crop'] = message
            
            try:
                precio_info = await maga_api.get_precio_cultivo(message)
                if precio_info:
                    user_data['precio_info'] = precio_info
                    logger.info(f"Precio encontrado para {message}: {precio_info}")
            except Exception as e:
                logger.error(f"Error obteniendo precios: {str(e)}")
            
            new_state = ConversationState.ASKING_AREA.value
            await WhatsAppService.send_message(from_number, MESSAGES['ask_area'])
            
        elif current_state == ConversationState.ASKING_AREA.value:
            # Guardar área
            try:
                area = float(message.replace('ha', '').strip())
                user_data['area'] = area
                new_state = ConversationState.ASKING_COMMERCIALIZATION.value
                await WhatsAppService.send_message(from_number, MESSAGES['ask_commercialization'])
            except ValueError:
                await WhatsAppService.send_message(from_number, MESSAGES['invalid_area'])
                return
                
        elif current_state == ConversationState.ASKING_COMMERCIALIZATION.value:
            # Guardar método de comercialización
            user_data['commercialization'] = message
            new_state = ConversationState.ASKING_IRRIGATION.value
            await WhatsAppService.send_message(from_number, MESSAGES['ask_irrigation'])
            
        elif current_state == ConversationState.ASKING_IRRIGATION.value:
            # Guardar sistema de riego
            user_data['irrigation'] = message
            new_state = ConversationState.ASKING_LOCATION.value
            await WhatsAppService.send_message(from_number, MESSAGES['ask_location'])
            
        elif current_state == ConversationState.ASKING_LOCATION.value:
            # Guardar ubicación y generar análisis
            user_data['location'] = message
            new_state = ConversationState.ANALYSIS.value
            
            # Generar y guardar análisis
            analysis = scoring_service.generate_analysis(user_data)
            firebase_manager.store_analysis(from_number, analysis)
            
            # Enviar resultados
            await WhatsAppService.send_message(from_number, MESSAGES['analysis_ready'])
            
        else:
            # Estado no reconocido, reiniciar
            firebase_manager.reset_user_state(from_number)
            await WhatsAppService.send_message(from_number, MESSAGES['error_restart'])
            return
            
        # Actualizar estado en Firebase
        firebase_manager.update_user_state(from_number, {
            'state': new_state,
            'data': user_data
        })
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        await WhatsAppService.send_message(from_number, MESSAGES['error'])

@app.post("/webhook/whatsapp")
async def webhook(request: Request):
    """
    Endpoint para recibir webhooks de WhatsApp
    """
    try:
        # Obtener y loguear el body raw
        body = await request.body()
        logger.info(f"Webhook raw body: {body}")
        
        # Parsear el JSON
        data = json.loads(body)
        
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
                                    logger.info(f"Mensaje de texto recibido - De: {from_number}, Contenido: {message_text}")
                                    await process_user_message(from_number, message_text)
                                    messages_processed += 1
        
        logger.info(f"Procesados {messages_processed} mensajes exitosamente")
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """
    Endpoint para verificar webhook de WhatsApp
    """
    try:
        verify_token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        if verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            return int(challenge)
        else:
            return JSONResponse(
                status_code=403,
                content={"status": "error", "message": "Invalid verify token"}
            )
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado del servicio
    """
    return {"status": "healthy"}
