from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from app.services.whatsapp_service import WhatsAppCloudAPI
import json
import os

load_dotenv()

app = FastAPI(title="Fingro API")
whatsapp = WhatsAppCloudAPI()

@app.get("/")
async def root():
    return {"message": "Fingro WhatsApp API"}

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """
    Endpoint para verificar el webhook con Meta
    """
    try:
        # Obtener parámetros de la URL
        params = dict(request.query_params)
        verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        
        print(f"Verificando webhook:")
        print(f"- Mode: {params.get('hub.mode')}")
        print(f"- Token: {params.get('hub.verify_token')}")
        print(f"- Challenge: {params.get('hub.challenge')}")
        
        # Verificar el token
        if params.get('hub.mode') == 'subscribe' and params.get('hub.verify_token') == verify_token:
            challenge = params.get('hub.challenge')
            return int(challenge)
        else:
            print(f"Verificación fallida:")
            print(f"- Token esperado: {verify_token}")
            print(f"- Token recibido: {params.get('hub.verify_token')}")
            raise HTTPException(status_code=403, detail="Verification failed")
            
    except Exception as e:
        print(f"Error verificando webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint para recibir mensajes de WhatsApp
    """
    try:
        # Obtener los datos del webhook
        data = await request.json()
        print(f"Datos recibidos en webhook POST: {json.dumps(data, indent=2)}")
        
        # Procesar el mensaje entrante
        try:
            # Extraer el mensaje y número de teléfono
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            print(f"Procesando entrada: {json.dumps(entry, indent=2)}")
            print(f"Cambios detectados: {json.dumps(changes, indent=2)}")
            print(f"Valor del cambio: {json.dumps(value, indent=2)}")
            
            if 'messages' in value:
                message = value['messages'][0]
                from_number = message['from']
                message_body = message.get('text', {}).get('body', '')
                
                print(f"\nMensaje recibido de {from_number}: {message_body}")
                
                # Enviar respuesta
                try:
                    response = whatsapp.send_text_message(
                        to_number=from_number,
                        message="¡Hola! 🌱 Bienvenido a Fingro. ¿Te gustaría saber cuánto podrías ganar con tu cosecha?"
                    )
                    print(f"Respuesta enviada exitosamente: {json.dumps(response, indent=2)}")
                except Exception as e:
                    print(f"Error enviando respuesta: {str(e)}")
                    if hasattr(e, 'response'):
                        print(f"Respuesta del error: {e.response.text}")
                    raise e
                
            return {"status": "success"}
            
        except Exception as e:
            print(f"Error procesando mensaje: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Respuesta del error: {e.response.text}")
            raise e
            
    except Exception as e:
        print(f"Error en webhook: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Respuesta del error: {e.response.text}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
