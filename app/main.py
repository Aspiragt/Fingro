from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
import json
import httpx
from typing import Dict, Any
from enum import Enum
from datetime import datetime
from .database import db
from .external_apis.maga import maga_client

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
        ConversationState.RIEGO: "¿Y ya tienes comprador para tu cosecha? ¿A quién le vendes normalmente?\nPor ejemplo: cooperativa, exportación, mercado local, intermediario, central de mayoreo",
        ConversationState.COMERCIALIZACION: "¿En qué municipio se encuentra o estará tu cultivo?",
        ConversationState.UBICACION: generate_summary(user_data),
        ConversationState.FINALIZADO: "¡Gracias por tu interés! Pronto un asesor se pondrá en contacto contigo."
    }
    return responses.get(state, "No entiendo ese estado.")

def generate_summary(user_data: Dict[str, Any]) -> str:
    """Genera un resumen de la información recopilada"""
    cultivo = user_data.get('cultivo', 'N/A')
    hectareas = user_data.get('hectareas', 'N/A')
    riego = user_data.get('riego', 'N/A')
    municipio = user_data.get('ubicacion', 'N/A')
    precio_info = user_data.get('precio_info', None)
    
    if precio_info:
        precio_actual = precio_info.get('precio_actual', 'N/A')
        unidad_medida = precio_info.get('unidad_medida', 'N/A')
        tendencia = precio_info.get('tendencia', 'N/A')
        ultima_actualizacion = precio_info.get('ultima_actualizacion', 'N/A')
        
        return f"""¡Gracias! Con la información que me has dado, puedo decirte que:

 Cultivo de {cultivo}
 {hectareas} hectáreas con riego por {riego}
 Ubicación: {municipio}
 Información del mercado:
 • Precio actual: Q.{precio_actual}/{unidad_medida}
 • Tendencia: {tendencia}
 • Última actualización: {ultima_actualizacion}
 Ingresos estimados: Q.80,000 (estimado)
 Costos estimados: Q.40,000 (estimado)

¿Te gustaría saber cuánto financiamiento podrías obtener?"""
    else:
        return f"""¡Gracias! Con la información que me has dado, puedo decirte que:

 Cultivo de {cultivo}
 {hectareas} hectáreas con riego por {riego}
 Ubicación: {municipio}
 Ingresos estimados: Q.80,000 (estimado)
 Costos estimados: Q.40,000 (estimado)

¿Te gustaría saber cuánto financiamiento podrías obtener?"""

async def process_user_message(from_number: str, message: str) -> str:
    """Procesa el mensaje del usuario y actualiza el estado de la conversación"""
    # Obtener o crear usuario
    user_data = await db.get_user(from_number)
    
    if not user_data:
        # Nuevo usuario
        user_data = {
            'estado_conversacion': ConversationState.INICIO,
            'data': {}
        }
        await db.create_or_update_user(from_number, user_data)
        return ("¡Bienvenido a Fingro! \n\n"
                "Somos tu aliado financiero en el campo. Te ayudamos a obtener el financiamiento que necesitas para tu cultivo "
                "de manera rápida y sencilla.\n\n"
                "En los próximos minutos, te haré algunas preguntas sobre tu proyecto agrícola. "
                "Con esta información, podremos:\n"
                "• Calcular el monto de financiamiento \n"
                "• Estimar los costos de producción \n"
                "• Proyectar tus ganancias potenciales \n\n"
                "Al final, recibirás un resumen detallado y nos pondremos en contacto contigo para discutir las opciones de financiamiento disponibles.\n\n"
                "¡Empecemos! ¿Qué cultivo estás planeando sembrar? ")
    
    current_state = ConversationState(user_data.get('estado_conversacion', ConversationState.INICIO))
    conversation_data = user_data.get('data', {})
    
    # Actualizar datos según el estado actual
    if current_state == ConversationState.INICIO:
        # Obtener información de precios del MAGA
        precio_info = await maga_client.get_precio_cultivo(message)
        
        # Guardar el cultivo
        conversation_data['cultivo'] = message
        user_data['estado_conversacion'] = ConversationState.CULTIVO
        
        # Construir respuesta con información de precios si está disponible
        response = f"Has seleccionado: {message}\n\n"
        
        if precio_info:
            response += (f" Información del mercado:\n"
                       f"• Precio actual: Q.{precio_info['precio_actual']}/{precio_info['unidad_medida']}\n"
                       f"• Tendencia: {precio_info['tendencia']}\n"
                       f"• Última actualización: {precio_info['ultima_actualizacion']}\n\n")
        
        response += "¿Cuántas hectáreas planeas cultivar?"
        
        # Actualizar usuario con la información de precios
        conversation_data['precio_info'] = precio_info if precio_info else None
        user_data['data'] = conversation_data
        await db.update_conversation_state(from_number, user_data)
        
        return response
        
    elif current_state == ConversationState.CULTIVO:
        conversation_data['hectareas'] = message
        user_data['estado_conversacion'] = ConversationState.HECTAREAS
        user_data['data'] = conversation_data
        await db.update_conversation_state(from_number, user_data)
        return get_response_for_state(ConversationState.HECTAREAS, conversation_data)
    
    elif current_state == ConversationState.HECTAREAS:
        conversation_data['riego'] = message
        user_data['estado_conversacion'] = ConversationState.RIEGO
        user_data['data'] = conversation_data
        await db.update_conversation_state(from_number, user_data)
        return get_response_for_state(ConversationState.RIEGO, conversation_data)
    
    elif current_state == ConversationState.RIEGO:
        conversation_data['comercializacion'] = message
        user_data['estado_conversacion'] = ConversationState.COMERCIALIZACION
        user_data['data'] = conversation_data
        await db.update_conversation_state(from_number, user_data)
        return get_response_for_state(ConversationState.COMERCIALIZACION, conversation_data)
    
    elif current_state == ConversationState.COMERCIALIZACION:
        conversation_data['ubicacion'] = message
        user_data['estado_conversacion'] = ConversationState.UBICACION
        user_data['data'] = conversation_data
        await db.update_conversation_state(from_number, user_data)
        return get_response_for_state(ConversationState.UBICACION, conversation_data)
    
    elif current_state == ConversationState.UBICACION:
        user_data['estado_conversacion'] = ConversationState.FINALIZADO
        user_data['data'] = conversation_data
        await db.update_conversation_state(from_number, user_data)
        return get_response_for_state(ConversationState.FINALIZADO, conversation_data)
    
    elif current_state == ConversationState.FINALIZADO:
        await db.create_solicitud(from_number, conversation_data)
        await db.delete_user_data(from_number)  # Borrar datos después de crear la solicitud
        return get_response_for_state(ConversationState.FINALIZADO, conversation_data)

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
