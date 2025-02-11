from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
import logging
import os
import json
import httpx
from typing import Dict, Any

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(title="Fingro Bot")

# Variables de WhatsApp Cloud API
WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = "v17.0"
WHATSAPP_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"

async def send_whatsapp_message(to_number: str, message: str) -> Dict:
    """Enviar mensaje usando WhatsApp Cloud API"""
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
        async with httpx.AsyncClient() as client:
            logger.debug(f"Enviando mensaje a WhatsApp: {json.dumps(payload, indent=2)}")
            response = await client.post(WHATSAPP_URL, json=payload, headers=headers)
            response_json = response.json()
            logger.debug(f"Respuesta de WhatsApp: {json.dumps(response_json, indent=2)}")
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
    """Verificar webhook de WhatsApp Cloud API"""
    try:
        # Los parámetros que WhatsApp envía para la verificación
        params = dict(request.query_params)
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "fingro-bot-token")
        
        if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
            challenge = params.get("hub.challenge")
            return Response(content=challenge, media_type="text/plain")
            
        return Response(status_code=403)
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook(request: Request):
    """Recibir mensajes de WhatsApp Cloud API"""
    try:
        body = await request.json()
        logger.debug(f"Webhook recibido: {json.dumps(body, indent=2)}")
        
        if body.get("object") != "whatsapp_business_account":
            return JSONResponse({"status": "not whatsapp"})
            
        # Procesar mensajes
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("value", {}).get("messages"):
                    for message in change["value"]["messages"]:
                        # Solo procesar mensajes de texto
                        if message.get("type") == "text":
                            from_number = message["from"]
                            text = message["text"]["body"]
                            logger.info(f"Mensaje recibido de {from_number}: {text}")
                            
                            # Enviar respuesta
                            response = "¡Hola! Gracias por tu mensaje. Soy el bot de Fingro 🌱"
                            await send_whatsapp_message(from_number, response)
        
        return JSONResponse({"status": "processed"})
        
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
