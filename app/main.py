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
import re

from app.config import settings
from app.services.whatsapp_service import WhatsAppService
from app.external_apis.maga import maga_api
from app.analysis.scoring import ScoringService
from app.database.firebase import firebase_manager
from app.utils import (
    ConversationState, 
    MESSAGES,
    format_currency,
    normalize_crop,
    normalize_irrigation,
    normalize_commercialization,
    normalize_yes_no
)

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
scoring_service = ScoringService()

# Estado de conversaciones
conversations: Dict[str, Dict[str, Any]] = {}

async def verify_webhook_signature(request: Request) -> bool:
    """
    Verifica la firma del webhook de WhatsApp
    
    Args:
        request: Request de FastAPI
        
    Returns:
        bool: True si la firma es válida
    """
    # En desarrollo, no verificar firma
    if settings.ENV != "production":
        return True
        
    try:
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not signature or not signature.startswith('sha256='):
            logger.warning("Firma no encontrada o inválida")
            return False
            
        # Si no hay secreto configurado, no verificar
        if not settings.WHATSAPP_WEBHOOK_SECRET:
            logger.warning("WHATSAPP_WEBHOOK_SECRET no configurado, saltando verificación")
            return True
            
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
        is_valid = hmac.compare_digest(calculated_signature, expected_signature)
        if not is_valid:
            logger.warning("Firma inválida")
        return is_valid
        
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
            # Guardar cultivo y obtener precio
            message = normalize_crop(message)
            if not message:
                await whatsapp.send_message(from_number, MESSAGES['unknown'])
                return
                
            user_data['crop'] = message
            
            try:
                precio = await maga_api.get_precio_cultivo(message)
                user_data['precio'] = precio
                logger.info(f"Precio obtenido para {message}: Q{precio}")
            except Exception as e:
                logger.error(f"Error obteniendo precio: {str(e)}")
                await whatsapp.send_message(from_number, MESSAGES['error'])
                return
                
            new_state = ConversationState.ASKING_AREA.value
            await whatsapp.send_message(from_number, MESSAGES['ask_area'])
            
        elif current_state == ConversationState.ASKING_AREA.value:
            # Validar y guardar área
            try:
                # Extraer el primer número del mensaje usando regex
                import re
                number_match = re.search(r'\d+\.?\d*', message)
                if not number_match:
                    raise ValueError("No se encontró un número válido")
                
                area = float(number_match.group())
                if area <= 0:
                    raise ValueError("Área debe ser mayor a 0")
                    
                user_data['area'] = area
                new_state = ConversationState.ASKING_IRRIGATION.value
                await whatsapp.send_message(from_number, MESSAGES['ask_irrigation'])
            except ValueError as e:
                await whatsapp.send_message(from_number, MESSAGES['invalid_area'])
                return
                
        elif current_state == ConversationState.ASKING_IRRIGATION.value:
            # Validar y guardar sistema de riego
            message = normalize_irrigation(message)
            if not message:
                await whatsapp.send_message(from_number, MESSAGES['unknown'])
                return
                
            user_data['irrigation'] = message
            new_state = ConversationState.ASKING_COMMERCIALIZATION.value
            await whatsapp.send_message(from_number, MESSAGES['ask_commercialization'])
            
        elif current_state == ConversationState.ASKING_COMMERCIALIZATION.value:
            # Guardar método de comercialización
            message = normalize_commercialization(message)
            valid_options = {
                'mercado local': 'mercado local',
                'intermediario': 'intermediario',
                'exportacion': 'exportacion',
                'directo': 'directo'
            }
            
            if message not in valid_options.values():
                await whatsapp.send_message(from_number, MESSAGES['unknown'])
                return
                
            user_data['commercialization'] = message
            new_state = ConversationState.ASKING_LOCATION.value
            await whatsapp.send_message(from_number, MESSAGES['ask_location'])
            
        elif current_state == ConversationState.ASKING_LOCATION.value:
            # Guardar ubicación y realizar análisis
            user_data['location'] = message
            
            try:
                # Obtener precio actual
                precio = await maga_api.get_precio_cultivo(user_data['crop'])
                logger.info(f"Precio obtenido para {user_data['crop']}: Q{precio}")
                
                # Calcular score y análisis
                score = await scoring_service.calculate_score(
                    data={
                        'crop': user_data['crop'],
                        'area': float(user_data['area']),
                        'irrigation': user_data['irrigation'],
                        'commercialization': user_data['commercialization']
                    },
                    precio_actual=precio
                )
                
                user_data['score'] = score
                new_state = ConversationState.ASKING_LOAN_INTEREST.value
                
                # Enviar análisis financiero
                await whatsapp.send_message(
                    from_number,
                    MESSAGES['analysis'].format(
                        cultivo=user_data['crop'].capitalize(),
                        area=user_data['area'],
                        ingresos=format_currency(score['expected_income']),
                        costos=format_currency(score['estimated_costs']),
                        ganancia=format_currency(score['expected_profit'])
                    )
                )
                
                # Preguntar si está interesado en el préstamo
                await whatsapp.send_message(
                    from_number,
                    MESSAGES['ask_loan_interest']
                )
                
            except Exception as e:
                logger.error(f"Error en análisis: {str(e)}")
                await whatsapp.send_message(from_number, MESSAGES['error'])
                return
                
        elif current_state == ConversationState.ASKING_LOAN_INTEREST.value:
            # Procesar interés en préstamo
            message = normalize_yes_no(message)
            if message == 'si':
                await whatsapp.send_message(from_number, MESSAGES['loan_yes'])
                new_state = ConversationState.COMPLETED.value
            elif message == 'no':
                await whatsapp.send_message(from_number, MESSAGES['loan_no'])
                new_state = ConversationState.COMPLETED.value
            else:
                await whatsapp.send_message(from_number, MESSAGES['ask_yes_no'])
                return
                
        else:
            logger.error(f"Estado no manejado: {current_state}")
            await whatsapp.send_message(from_number, MESSAGES['error'])
            return
            
        # Actualizar estado y datos
        conversation_data['state'] = new_state
        conversation_data['data'] = user_data
        await firebase_manager.update_user_state(from_number, conversation_data)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        await whatsapp.send_message(from_number, MESSAGES['error'])

@app.post("/webhook/whatsapp")
async def webhook(request: Request) -> Dict[str, str]:
    """
    Endpoint para recibir webhooks de WhatsApp
    """
    try:
        # Obtener datos del webhook
        body = await request.json()
        logger.info(f"Webhook recibido: {json.dumps(body, indent=2)}")

        # Procesar solo si es un mensaje
        if "entry" in body and body["entry"]:
            for entry in body["entry"]:
                if "changes" in entry and entry["changes"]:
                    for change in entry["changes"]:
                        if "value" in change and "messages" in change["value"]:
                            for message in change["value"]["messages"]:
                                # Extraer información del mensaje
                                from_number = message["from"]
                                message_text = message.get("text", {}).get("body", "")
                                
                                logger.info(f"Mensaje recibido de {from_number}: {message_text}")
                                
                                # Procesar mensaje
                                await process_user_message(from_number, message_text)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    """
    Ruta raíz que muestra información básica de la API
    """
    return {
        "name": "FinGro API",
        "version": "1.0.0",
        "status": "running",
        "env": settings.ENV
    }

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """
    Endpoint para verificar webhook de WhatsApp
    """
    try:
        # Obtener parámetros
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')
        
        # Verificar modo y token
        if mode == 'subscribe' and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            if not challenge:
                raise HTTPException(
                    status_code=400,
                    detail="No challenge received"
                )
                
            logger.info("Webhook verificado exitosamente")
            return Response(content=challenge)
            
        raise HTTPException(status_code=403, detail="Invalid verification token")
        
    except Exception as e:
        logger.error(f"Error en verificación de webhook: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado del servicio
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Obtener puerto de Render o usar 8000 por defecto
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENV == "development"
    )
