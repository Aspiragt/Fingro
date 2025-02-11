from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
import logging
import os
import json
import httpx
from typing import Dict, Any

# Configuración detallada de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(title="Fingro Bot")

# Variables de WhatsApp
WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_URL = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

async def send_whatsapp_message(to_number: str, message: str) -> Dict:
    """Enviar mensaje de WhatsApp"""
    logger.info(f"Enviando mensaje a {to_number}: {message}")
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Enviando request a WhatsApp API: {json.dumps(payload, indent=2)}")
            response = await client.post(WHATSAPP_URL, json=payload, headers=headers)
            response_json = response.json()
            logger.info(f"Respuesta de WhatsApp API: {json.dumps(response_json, indent=2)}")
            return response_json
    except Exception as e:
        logger.error(f"Error enviando mensaje: {str(e)}")
        raise

@app.get("/")
async def health_check():
    """Verificar que el servicio está funcionando"""
    status = {
        "status": "healthy",
        "service": "fingro-bot",
        "whatsapp_configured": bool(WHATSAPP_TOKEN and PHONE_NUMBER_ID)
    }
    logger.info(f"Health check: {json.dumps(status, indent=2)}")
    return status

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Verificar webhook de WhatsApp"""
    try:
        params = dict(request.query_params)
        logger.info(f"Verificación de webhook recibida: {params}")
        if params.get("hub.mode") == "subscribe":
            return Response(content=params.get("hub.challenge"), media_type="text/plain")
        return Response(status_code=403)
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook(request: Request):
    """Recibir mensajes de WhatsApp"""
    try:
        body = await request.json()
        logger.info(f"Webhook recibido: {json.dumps(body, indent=2)}")
        
        # Verificar que es un evento de WhatsApp
        if body.get("object") != "whatsapp_business_account":
            logger.warning("Evento no es de WhatsApp Business")
            return JSONResponse({"status": "not whatsapp"})
            
        # Procesar mensajes
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            logger.info("No hay mensajes para procesar")
            return {"status": "no messages"}
            
        # Procesar cada mensaje
        for message in messages:
            from_number = message.get("from")
            if message.get("type") == "text":
                text = message.get("text", {}).get("body", "")
                logger.info(f"Mensaje recibido de {from_number}: {text}")
                
                # Respuesta simple
                response = "¡Hola! Gracias por tu mensaje. Soy el bot de Fingro 🌱"
                await send_whatsapp_message(from_number, response)
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
