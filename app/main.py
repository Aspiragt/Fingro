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

async def verify_webhook_signature(request: Request) -> bool:
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
            logger.warning("Firma no encontrada o inválida")
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
            # Mensaje de bienvenida
            user_data['name'] = message
            new_state = ConversationState.ASKING_CROP.value
            await whatsapp.send_message(from_number, MESSAGES['ask_crop'])
            
        elif current_state == ConversationState.ASKING_CROP.value:
            # Guardar cultivo y obtener precio
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
                area = float(message)
                if area <= 0:
                    raise ValueError("Área debe ser mayor a 0")
                user_data['area'] = area
                new_state = ConversationState.ASKING_IRRIGATION.value
                await whatsapp.send_message(from_number, MESSAGES['ask_irrigation'])
            except ValueError:
                await whatsapp.send_message(from_number, MESSAGES['invalid_area'])
                return
                
        elif current_state == ConversationState.ASKING_IRRIGATION.value:
            # Guardar método de riego
            message = message.lower().strip()
            if message not in ['goteo', 'aspersion', 'gravedad', 'temporal']:
                await whatsapp.send_message(
                    from_number, 
                    "❌ Método de riego inválido. Opciones: goteo, aspersion, gravedad, temporal"
                )
                return
                
            user_data['irrigation'] = message
            new_state = ConversationState.ASKING_COMMERCIALIZATION.value
            await whatsapp.send_message(from_number, MESSAGES['ask_commercialization'])
            
        elif current_state == ConversationState.ASKING_COMMERCIALIZATION.value:
            # Guardar método de comercialización
            message = message.lower().strip()
            if message not in ['mercado local', 'exportacion', 'intermediario', 'directo']:
                await whatsapp.send_message(
                    from_number,
                    "❌ Método inválido. Opciones: mercado local, exportacion, intermediario, directo"
                )
                return
                
            user_data['commercialization'] = message
            new_state = ConversationState.ASKING_LOCATION.value
            await whatsapp.send_message(from_number, MESSAGES['ask_location'])
            
        elif current_state == ConversationState.ASKING_LOCATION.value:
            # Guardar ubicación y realizar análisis
            user_data['location'] = message
            
            try:
                # Obtener datos históricos
                datos_historicos = await maga_api.get_datos_historicos(user_data['crop'])
                if not datos_historicos:
                    raise ValueError(f"No hay datos para el cultivo: {user_data['crop']}")
                    
                # Calcular score y análisis
                score = scoring_service.calculate_score(
                    crop=user_data['crop'],
                    area=user_data['area'],
                    irrigation=user_data['irrigation'],
                    commercialization=user_data['commercialization'],
                    historical_data=datos_historicos
                )
                
                user_data['score'] = score
                new_state = ConversationState.ASKING_LOAN_INTEREST.value
                
                # Enviar resultado
                await whatsapp.send_message(
                    from_number,
                    MESSAGES['analysis_ready'].format(
                        score=score['total'],
                        monto=score['suggested_loan']
                    )
                )
                
            except Exception as e:
                logger.error(f"Error en análisis: {str(e)}")
                await whatsapp.send_message(from_number, MESSAGES['error'])
                return
                
        elif current_state == ConversationState.ASKING_LOAN_INTEREST.value:
            # Procesar interés en préstamo
            message = message.lower().strip()
            if message == 'si':
                await whatsapp.send_message(from_number, MESSAGES['loan_yes'])
                new_state = ConversationState.COMPLETED.value
            elif message == 'no':
                await whatsapp.send_message(from_number, MESSAGES['loan_no'])
                new_state = ConversationState.COMPLETED.value
            else:
                await whatsapp.send_message(
                    from_number,
                    "❌ Por favor responde 'si' o 'no'"
                )
                return
                
        else:
            logger.error(f"Estado no manejado: {current_state}")
            await whatsapp.send_message(from_number, MESSAGES['error'])
            return
            
        # Actualizar estado
        await firebase_manager.update_conversation_state(
            from_number,
            new_state,
            user_data
        )
        
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
        "env": settings.ENV
    }

@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint para recibir webhooks de WhatsApp
    """
    try:
        # Verificar firma
        if not await verify_webhook_signature(request):
            logger.warning("Firma inválida en webhook")
            raise HTTPException(status_code=401, detail="Invalid signature")
            
        # Obtener datos
        data = await request.json()
        logger.debug(f"Webhook recibido: {json.dumps(data, indent=2)}")
        
        # Verificar tipo de evento
        if data.get('object') != 'whatsapp_business_account':
            logger.warning(f"Objeto no soportado: {data.get('object')}")
            return Response(status_code=202)
            
        # Procesar cada entrada
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('value', {}).get('messages'):
                    for message in change['value']['messages']:
                        # Obtener número y mensaje
                        from_number = message['from']
                        message_text = message.get('text', {}).get('body', '')
                        
                        # Procesar mensaje
                        await process_user_message(from_number, message_text)
        
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/webhook")
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
