from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
import logging
import os
import json
import httpx
from typing import Dict, Any
from enum import Enum
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(title="Fingro Bot")

# Variables de WhatsApp Cloud API
WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = "v17.0"
WHATSAPP_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"

# Estados de la conversación
class ConversationState(str, Enum):
    INICIO = "INICIO"
    CULTIVO = "CULTIVO"
    HECTAREAS = "HECTAREAS"
    RIEGO = "RIEGO"
    COMERCIALIZACION = "COMERCIALIZACION"
    UBICACION = "UBICACION"
    FINALIZADO = "FINALIZADO"

# Almacenamiento temporal de conversaciones
# En producción, esto debería estar en una base de datos
conversations: Dict[str, Dict[str, Any]] = {}

def get_next_state(current_state: ConversationState) -> ConversationState:
    """Determina el siguiente estado de la conversación"""
    state_flow = {
        ConversationState.INICIO: ConversationState.CULTIVO,
        ConversationState.CULTIVO: ConversationState.HECTAREAS,
        ConversationState.HECTAREAS: ConversationState.RIEGO,
        ConversationState.RIEGO: ConversationState.COMERCIALIZACION,
        ConversationState.COMERCIALIZACION: ConversationState.UBICACION,
        ConversationState.UBICACION: ConversationState.FINALIZADO,
        ConversationState.FINALIZADO: ConversationState.FINALIZADO,
    }
    return state_flow.get(current_state, ConversationState.INICIO)

def get_response_for_state(state: ConversationState, user_data: Dict[str, Any]) -> str:
    """Genera la respuesta apropiada según el estado de la conversación"""
    responses = {
        ConversationState.INICIO: "¡Hola! Soy Fingro , tu asistente para conseguir financiamiento agrícola. ¿Qué te gustaría cultivar?",
        ConversationState.CULTIVO: f"¡Excelente elección! ¿Cuántas hectáreas planeas cultivar?",
        ConversationState.HECTAREAS: "Entiendo. ¿Qué método de riego utilizas o planeas utilizar?\nPor ejemplo: por goteo, aspersión, o tradicional",
        ConversationState.RIEGO: "¿Y ya tienes comprador para tu cosecha? ¿A quién le vendes normalmente?",
        ConversationState.COMERCIALIZACION: "¿Te gustaría compartir tu ubicación para que pueda darte información más precisa?",
        ConversationState.UBICACION: generate_summary(user_data),
        ConversationState.FINALIZADO: "¡Gracias por tu interés! Pronto un asesor se pondrá en contacto contigo."
    }
    return responses.get(state, "No entiendo ese estado.")

def generate_summary(user_data: Dict[str, Any]) -> str:
    """Genera un resumen de la información recopilada"""
    # TODO: Integrar con APIs para obtener precios y costos reales
    cultivo = user_data.get('cultivo', 'N/A')
    hectareas = user_data.get('hectareas', 'N/A')
    riego = user_data.get('riego', 'N/A')
    
    return f"""¡Gracias! Con la información que me has dado, puedo decirte que:

 Cultivo de {cultivo}
 {hectareas} hectáreas con riego por {riego}
 Ingresos estimados: $10,000 (estimado)
 Costos estimados: $5,000 (estimado)

¿Te gustaría saber cuánto financiamiento podrías obtener?"""

def process_user_message(from_number: str, message: str) -> str:
    """Procesa el mensaje del usuario y actualiza el estado de la conversación"""
    # Obtener o crear la conversación del usuario
    if from_number not in conversations:
        conversations[from_number] = {
            'state': ConversationState.INICIO,
            'data': {},
            'last_update': datetime.now().isoformat()
        }
    
    conversation = conversations[from_number]
    current_state = ConversationState(conversation['state'])
    
    # Actualizar datos según el estado actual
    if current_state == ConversationState.INICIO:
        conversation['data']['cultivo'] = message
    elif current_state == ConversationState.CULTIVO:
        conversation['data']['hectareas'] = message
    elif current_state == ConversationState.HECTAREAS:
        conversation['data']['riego'] = message
    elif current_state == ConversationState.RIEGO:
        conversation['data']['comercializacion'] = message
    elif current_state == ConversationState.COMERCIALIZACION:
        conversation['data']['ubicacion'] = message
    
    # Avanzar al siguiente estado
    next_state = get_next_state(current_state)
    conversation['state'] = next_state
    conversation['last_update'] = datetime.now().isoformat()
    
    # Generar respuesta
    return get_response_for_state(next_state, conversation['data'])

async def send_whatsapp_message(to_number: str, message: str) -> Dict:
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
                                response = process_user_message(from_number, text)
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
