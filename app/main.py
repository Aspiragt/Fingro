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
from app.database.firebase import FirebaseDB
from app.external_apis.maga import maga_client
from app.analysis.scoring import scoring
from app.views.financial_report import report_generator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI()

# Inicializar servicios
db = FirebaseDB()
whatsapp_service = WhatsAppService()

# Variables de WhatsApp Cloud API
WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = "v17.0"
WHATSAPP_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"

async def get_response_for_state(state: ConversationState, user_data: dict[str, Any]) -> str:
    """Genera la respuesta apropiada según el estado de la conversación"""
    try:
        if state == ConversationState.FINALIZADO:
            # Calcular Fingro Score
            score_data = scoring.calculate_score(user_data)
            if not score_data:
                return "❌ Lo siento, hubo un error al analizar tu proyecto. Por favor, escribe 'reiniciar' para intentar de nuevo."
            
            # Generar reporte detallado
            return report_generator.generate_detailed_report(user_data, score_data)
        else:
            # Usar mensajes predefinidos para otros estados
            message = MESSAGES.get(state)
            if callable(message):
                return message(user_data)
            return message
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        return "❌ Lo siento, ocurrió un error. Por favor, escribe 'reiniciar' para intentar de nuevo."

async def process_user_message(from_number: str, message: str) -> str:
    """
    Procesa el mensaje del usuario y actualiza el estado de la conversación
    """
    try:
        # Obtener estado actual
        conversation_data = db.get_conversation_state(from_number)
        
        # Si no hay datos de conversación, inicializar con estado INICIO
        if not conversation_data:
            conversation_data = {'state': ConversationState.INICIO, 'data': {}}
            db.update_conversation_state(from_number, conversation_data)
        
        current_state = conversation_data.get('state', ConversationState.INICIO)
        user_data = conversation_data.get('data', {})
        
        # Si el mensaje es 'reiniciar', volver al inicio
        if message.lower() == 'reiniciar':
            new_conversation_data = {'state': ConversationState.INICIO, 'data': {}}
            db.update_conversation_state(from_number, new_conversation_data)
            return await get_response_for_state(ConversationState.INICIO, {})
            
        # Procesar mensaje según el estado actual
        if current_state == ConversationState.INICIO:
            # Guardar cultivo y buscar datos
            cultivo = message.strip()
            user_data['cultivo'] = cultivo
            
            try:
                # Obtener precio del MAGA
                precio_info = await maga_client.get_precio_cultivo(cultivo)
                if precio_info:
                    user_data['precio_info'] = precio_info
                    logger.info(f"Precio encontrado para {cultivo}: {precio_info}")
                else:
                    # Si no hay precio en MAGA, usar precio por defecto
                    user_data['precio_info'] = {
                        'precio_actual': 150,  # Precio por defecto
                        'tendencia': 'estable',
                        'unidad_medida': 'quintal'
                    }
                    logger.warning(f"No se encontró precio para {cultivo}, usando valor por defecto")
            except Exception as e:
                logger.error(f"Error obteniendo precios: {str(e)}")
                # Si hay error, usar precio por defecto
                user_data['precio_info'] = {
                    'precio_actual': 150,
                    'tendencia': 'estable',
                    'unidad_medida': 'quintal'
                }
            
            new_conversation_data = {'state': ConversationState.CULTIVO, 'data': user_data}
            db.update_conversation_state(from_number, new_conversation_data)
            return await get_response_for_state(ConversationState.CULTIVO, user_data)
            
        elif current_state == ConversationState.CULTIVO:
            try:
                hectareas = float(message.replace(',', '.'))
                if hectareas <= 0:
                    return "Por favor, ingresa un número válido mayor a 0"
            except ValueError:
                return "Por favor, ingresa un número válido. Por ejemplo: 2.5"
                
            user_data['hectareas'] = hectareas
            new_conversation_data = {'state': ConversationState.HECTAREAS, 'data': user_data}
            db.update_conversation_state(from_number, new_conversation_data)
            return await get_response_for_state(ConversationState.HECTAREAS, user_data)
        
        elif current_state == ConversationState.HECTAREAS:
            user_data['riego'] = message
            new_conversation_data = {'state': ConversationState.RIEGO, 'data': user_data}
            db.update_conversation_state(from_number, new_conversation_data)
            return await get_response_for_state(ConversationState.RIEGO, user_data)
        
        elif current_state == ConversationState.RIEGO:
            user_data['comercializacion'] = message
            new_conversation_data = {'state': ConversationState.COMERCIALIZACION, 'data': user_data}
            db.update_conversation_state(from_number, new_conversation_data)
            return await get_response_for_state(ConversationState.COMERCIALIZACION, user_data)
        
        elif current_state == ConversationState.COMERCIALIZACION:
            user_data['ubicacion'] = message
            new_conversation_data = {'state': ConversationState.FINALIZADO, 'data': user_data}
            db.update_conversation_state(from_number, new_conversation_data)
            
            # Generar y enviar el análisis final
            return await get_response_for_state(ConversationState.FINALIZADO, user_data)
        
        elif current_state == ConversationState.FINALIZADO:
            return "Tu análisis ya está listo. Si quieres iniciar una nueva consulta, escribe 'reiniciar'."
            
        else:
            return "Lo siento, ha ocurrido un error. Por favor escribe 'reiniciar' para comenzar de nuevo."
            
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
        return "Lo siento, ha ocurrido un error. Por favor escribe 'reiniciar' para comenzar de nuevo."

async def send_whatsapp_message(to_number: str, message: str) -> dict:
    """Enviar mensaje usando WhatsApp Cloud API"""
    logger.info(f"Intentando enviar mensaje a {to_number}")
    
    # Asegurarse de que el número tenga el formato correcto
    if to_number.startswith("+"):
        to_number = to_number[1:]
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        logger.debug(f"Payload del mensaje: {json.dumps(payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            logger.info(f"Enviando request a: {WHATSAPP_URL}")
            response = await client.post(WHATSAPP_URL, json=payload, headers=headers)
            response_json = response.json()
            
            logger.info(f"Respuesta de WhatsApp [Status: {response.status_code}]: {json.dumps(response_json, indent=2)}")
            
            if response.status_code != 200:
                logger.error(f"Error en la respuesta de WhatsApp: {response_json}")
            
            return response_json
    except Exception as e:
        logger.error(f"Error enviando mensaje: {str(e)}", exc_info=True)
        raise

@app.get("/")
async def root():
    """Endpoint de prueba"""
    logger.info("Acceso al endpoint raíz")
    return {
        "status": "healthy",
        "service": "fingro-bot",
        "whatsapp_configured": bool(WHATSAPP_TOKEN and PHONE_NUMBER_ID)
    }

@app.get("/health")
async def health_check():
    """Endpoint para health check de Render"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """Verificar webhook de WhatsApp Cloud API"""
    try:
        params = dict(request.query_params)
        logger.info(f"Verificación de webhook recibida. Parámetros: {params}")
        
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "fingro-bot-token")
        logger.debug(f"Token de verificación esperado: {verify_token}")
        
        if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
            challenge = params.get("hub.challenge")
            logger.info(f"Verificación exitosa. Challenge: {challenge}")
            return Response(content=challenge, media_type="text/plain")
        
        logger.warning("Verificación fallida: token no coincide o modo incorrecto")
        return Response(status_code=403)
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/whatsapp")
async def webhook(request: Request):
    """Recibir mensajes de WhatsApp Cloud API"""
    try:
        # Obtener el cuerpo de la petición como texto
        body_str = await request.body()
        logger.info(f"Webhook raw body: {body_str}")
        
        # Convertir a JSON
        try:
            body = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid JSON"}
            )
        
        logger.info("Webhook recibido")
        logger.debug(f"Contenido del webhook: {json.dumps(body, indent=2)}")
        
        # Verificar que es un evento de WhatsApp
        if body.get("object") != "whatsapp_business_account":
            logger.warning(f"Objeto incorrecto recibido: {body.get('object')}")
            return JSONResponse({"status": "not whatsapp"})
        
        # Procesar mensajes
        messages_processed = 0
        try:
            entries = body.get("entry", [])
            logger.debug(f"Procesando {len(entries)} entries")
            
            for entry in entries:
                changes = entry.get("changes", [])
                logger.debug(f"Procesando {len(changes)} changes en entry {entry.get('id')}")
                
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    logger.debug(f"Procesando {len(messages)} mensajes en change")
                    
                    for message in messages:
                        if message.get("type") == "text":
                            from_number = message.get("from")
                            text = message.get("text", {}).get("body", "")
                            logger.info(f"Mensaje de texto recibido - De: {from_number}, Contenido: {text}")
                            
                            # Procesar el mensaje y obtener respuesta
                            try:
                                response = await process_user_message(from_number, text)
                                await send_whatsapp_message(from_number, response)
                                messages_processed += 1
                            except Exception as e:
                                logger.error(f"Error procesando mensaje: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error procesando mensajes: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing messages: {str(e)}"}
            )
        
        logger.info(f"Procesados {messages_processed} mensajes exitosamente")
        return JSONResponse({
            "status": "processed",
            "messages": messages_processed
        })
        
    except Exception as e:
        logger.error(f"Error general en webhook: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/test-send/{phone_number}")
async def test_send(phone_number: str):
    """Endpoint de prueba para enviar mensajes"""
    try:
        logger.info(f"Probando envío de mensaje a {phone_number}")
        response = await send_whatsapp_message(
            phone_number,
            "Este es un mensaje de prueba desde Fingro Bot "
        )
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        logger.error(f"Error en prueba: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
