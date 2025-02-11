"""
FastAPI app principal
"""
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Optional
import logging
import os
import json
import httpx
from enum import Enum
from datetime import datetime
from .database import db
from .external_apis.maga import maga_client
from .analysis.financial import financial_analyzer

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
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

async def get_response_for_state(state: ConversationState, user_data: dict[str, Any]) -> str:
    """Genera la respuesta apropiada según el estado de la conversación"""
    responses = {
        ConversationState.INICIO: "¡Hola! Soy Fingro, tu asistente para conseguir financiamiento agrícola. ¿Qué te gustaría cultivar?",
        ConversationState.CULTIVO: "¡Excelente elección! ¿Cuántas hectáreas planeas cultivar?",
        ConversationState.HECTAREAS: "Entiendo. ¿Qué método de riego utilizas o planeas utilizar?\nPor ejemplo: por goteo, aspersión, o tradicional",
        ConversationState.RIEGO: "¿Y ya tienes comprador para tu cosecha? ¿A quién le vendes normalmente?\nPor ejemplo: cooperativa, exportación, mercado local, intermediario, central de mayoreo",
        ConversationState.COMERCIALIZACION: "¿En qué municipio está o estará ubicado el cultivo?",
        ConversationState.UBICACION: "¡Perfecto! Dame un momento para analizar tu proyecto...",
        ConversationState.FINALIZADO: None  # Se genera dinámicamente
    }
    
    if state != ConversationState.FINALIZADO:
        return responses[state]
    
    try:
        # Si es el estado FINALIZADO, generar resumen
        cultivo = user_data.get('cultivo', 'N/A')
        hectareas = float(user_data.get('hectareas', 0))
        riego = user_data.get('riego', 'tradicional')
        comercializacion = user_data.get('comercializacion', 'N/A')
        municipio = user_data.get('ubicacion', 'N/A')
        precio_info = user_data.get('precio_info', {})
        
        # Realizar análisis financiero
        precio_actual = precio_info.get('precio_actual', 150)  # Precio por defecto si no hay datos del MAGA
        logger.info(f"Iniciando análisis financiero para cultivo={cultivo}, hectareas={hectareas}, precio={precio_actual}, riego={riego}")
        
        analisis = await financial_analyzer.analizar_proyecto(cultivo, hectareas, precio_actual, riego)
        if not analisis:
            logger.error(f"No se pudo obtener análisis financiero para el cultivo: {cultivo}")
            return ("Lo siento, no pudimos analizar este cultivo en este momento. "
                   "Por favor, escribe 'reiniciar' para intentar con otro cultivo o contacta a nuestro equipo de soporte.")
        
        resumen = analisis['resumen_financiero']
        detalle = analisis['analisis_detallado']
        
        # Calcular valores simplificados
        costo_total = resumen['inversion_requerida']
        produccion_total = detalle['rendimiento_total_min']  # Usamos el mínimo para ser conservadores
        venta_total = produccion_total * precio_actual
        ganancia = venta_total - costo_total
        margen = (ganancia / venta_total) * 100 if venta_total > 0 else 0
        
        return (f"¡Excelente! Aquí está el análisis de tu proyecto:\n\n"
                f"📊 Resumen del Proyecto:\n"
                f"• Cultivo: {cultivo}\n"
                f"• Área: {hectareas} hectáreas\n"
                f"• Riego: {riego}\n"
                f"• Comercialización: {comercializacion}\n"
                f"• Ubicación: {municipio}\n\n"
                f"💰 Análisis Financiero:\n"
                f"• Inversión Requerida: Q.{costo_total:,.2f}\n"
                f"• Venta Proyectada: Q.{venta_total:,.2f}\n"
                f"• Ganancia Estimada: Q.{ganancia:,.2f}\n"
                f"• Margen de Ganancia: {margen:.1f}%\n\n"
                f"🌱 Próximos Pasos:\n"
                f"1. Nuestro equipo se pondrá en contacto contigo pronto para discutir las opciones de financiamiento.\n"
                f"2. Prepara los siguientes documentos:\n"
                f"   • DPI\n"
                f"   • Comprobante de domicilio\n"
                f"   • Título de propiedad o contrato de arrendamiento\n\n"
                f"Si tienes preguntas o quieres iniciar una nueva consulta, escribe 'reiniciar'.")
    except Exception as e:
        logger.error(f"Error generando análisis financiero: {str(e)}")
        return ("Lo siento, hubo un error al analizar tu proyecto. "
               "Por favor, escribe 'reiniciar' para intentar de nuevo o contacta a nuestro equipo de soporte.")

async def process_user_message(from_number: str, message: str) -> str:
    """Procesa el mensaje del usuario y actualiza el estado de la conversación"""
    try:
        # Verificar si es un comando para reiniciar
        if message.strip().lower() in ['reiniciar', 'restart', 'comenzar', 'inicio']:
            # Reiniciar la conversación
            conversation_data = {}
            await db.update_conversation_state(from_number, ConversationState.INICIO, conversation_data)
            return ("¡Bienvenido a Fingro! \n\n"
                    "Somos tu aliado financiero en el campo. Te ayudamos a obtener el financiamiento que necesitas para tu cultivo "
                    "de manera rápida y sencilla.\n\n"
                    "En los próximos minutos, te haré algunas preguntas sobre tu proyecto agrícola. "
                    "Con esta información, podremos:\n"
                    "• Calcular el monto de financiamiento \n"
                    "• Estimar los costos de producción \n"
                    "• Proyectar tus ganancias potenciales \n\n"
                    "Al final, recibirás un resumen detallado y nos pondremos en contacto contigo para discutir las opciones de financiamiento disponibles.\n\n"
                    "¡Empecemos! ¿Qué cultivo estás planeando sembrar?")

        # Obtener datos del usuario
        user_data = await db.get_user(from_number) or {}
        current_state = ConversationState(user_data.get('estado_conversacion', ConversationState.INICIO))
        conversation_data = user_data.get('data', {})

        # Si es un usuario nuevo, enviar mensaje de bienvenida
        if not user_data:
            conversation_data = {}
            await db.update_conversation_state(from_number, ConversationState.INICIO, conversation_data)
            return ("¡Bienvenido a Fingro! \n\n"
                    "Somos tu aliado financiero en el campo. Te ayudamos a obtener el financiamiento que necesitas para tu cultivo "
                    "de manera rápida y sencilla.\n\n"
                    "En los próximos minutos, te haré algunas preguntas sobre tu proyecto agrícola. "
                    "Con esta información, podremos:\n"
                    "• Calcular el monto de financiamiento \n"
                    "• Estimar los costos de producción \n"
                    "• Proyectar tus ganancias potenciales \n\n"
                    "Al final, recibirás un resumen detallado y nos pondremos en contacto contigo para discutir las opciones de financiamiento disponibles.\n\n"
                    "¡Empecemos! ¿Qué cultivo estás planeando sembrar?")
        
        if current_state == ConversationState.INICIO:
            # Procesar cultivo
            cultivo = message.strip().lower()
            conversation_data['cultivo'] = cultivo
            
            # Obtener información de precios (solo guardar, no mostrar)
            try:
                precio_info = await maga_client.get_market_prices(cultivo)
                conversation_data['precio_info'] = precio_info if precio_info else None
            except Exception as e:
                logger.error(f"Error obteniendo precios: {str(e)}")
                conversation_data['precio_info'] = None
            
            next_state = ConversationState.CULTIVO
            await db.update_conversation_state(from_number, next_state, conversation_data)
            return await get_response_for_state(next_state, conversation_data)
            
        elif current_state == ConversationState.CULTIVO:
            try:
                hectareas = float(message.replace(',', '.'))
                if hectareas <= 0:
                    return "Por favor, ingresa un número válido mayor que 0."
            except ValueError:
                return "Por favor, ingresa un número válido. Por ejemplo: 2.5"
                
            conversation_data['hectareas'] = hectareas
            next_state = ConversationState.HECTAREAS
            await db.update_conversation_state(from_number, next_state, conversation_data)
            return await get_response_for_state(next_state, conversation_data)
        
        elif current_state == ConversationState.HECTAREAS:
            conversation_data['riego'] = message
            next_state = ConversationState.RIEGO
            await db.update_conversation_state(from_number, next_state, conversation_data)
            return await get_response_for_state(next_state, conversation_data)
        
        elif current_state == ConversationState.RIEGO:
            conversation_data['comercializacion'] = message
            next_state = ConversationState.COMERCIALIZACION
            await db.update_conversation_state(from_number, next_state, conversation_data)
            return await get_response_for_state(next_state, conversation_data)
        
        elif current_state == ConversationState.COMERCIALIZACION:
            conversation_data['ubicacion'] = message
            
            # Actualizar al estado final directamente
            next_state = ConversationState.FINALIZADO
            await db.update_conversation_state(from_number, next_state, conversation_data)
            
            # Generar y enviar el análisis final
            return await get_response_for_state(next_state, conversation_data)
        
        elif current_state == ConversationState.FINALIZADO:
            return "Tu análisis ya está listo. Si quieres iniciar una nueva consulta, escribe 'reiniciar'."
        
        else:
            return "Lo siento, no entiendo ese comando. Por favor, escribe 'reiniciar' para comenzar de nuevo."
            
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        return "Lo siento, hubo un error procesando tu mensaje. Por favor, escribe 'reiniciar' para comenzar de nuevo."

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
