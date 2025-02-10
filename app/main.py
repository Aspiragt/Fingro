from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from app.services.whatsapp_service import WhatsAppCloudAPI
import json
import os

load_dotenv()

app = FastAPI(title="Fingro API")
whatsapp = WhatsAppCloudAPI()

# Estado del usuario
user_states = {}

@app.get("/")
async def root():
    return {"message": "Fingro WhatsApp API"}

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """
    Endpoint para verificar el webhook con Meta
    """
    try:
        params = dict(request.query_params)
        verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        
        print(f"Verificando webhook:")
        print(f"- Mode: {params.get('hub.mode')}")
        print(f"- Token: {params.get('hub.verify_token')}")
        print(f"- Challenge: {params.get('hub.challenge')}")
        
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
        data = await request.json()
        print(f"\nDEBUG - Webhook data received: {json.dumps(data, indent=2)}")
        
        try:
            # Verificar si hay entradas
            if not data.get('entry'):
                print("DEBUG - No entries in webhook data")
                return {"status": "success"}
            
            entry = data['entry'][0]
            
            # Verificar si hay cambios
            if not entry.get('changes'):
                print("DEBUG - No changes in entry")
                return {"status": "success"}
            
            changes = entry['changes'][0]
            
            # Verificar si hay valor
            if not changes.get('value'):
                print("DEBUG - No value in changes")
                return {"status": "success"}
            
            value = changes['value']
            
            # Verificar si hay mensajes
            if not value.get('messages'):
                print("DEBUG - No messages in value")
                return {"status": "success"}
            
            message = value['messages'][0]
            
            # Obtener el número y el texto del mensaje
            from_number = message['from']
            
            # Verificar si es un mensaje de texto
            if message.get('type') != 'text':
                print(f"DEBUG - Message is not text type: {message.get('type')}")
                return {"status": "success"}
            
            if not message.get('text', {}).get('body'):
                print("DEBUG - No text body in message")
                return {"status": "success"}
            
            message_body = message['text']['body']
            
            print(f"\nDEBUG - Processing message:")
            print(f"From: {from_number}")
            print(f"Message: {message_body}")
            
            # Procesar mensaje y obtener respuesta
            response_message = await whatsapp.process_message(from_number, message_body)
            
            print(f"\nDEBUG - Sending response: {response_message}")
            
            # Enviar respuesta
            try:
                response = whatsapp.send_text_message(
                    to_number=from_number,
                    message=response_message
                )
                print(f"DEBUG - Response sent successfully: {json.dumps(response, indent=2)}")
                
            except Exception as e:
                print(f"Error sending response: {str(e)}")
                if hasattr(e, 'response'):
                    print(f"Error response: {e.response.text}")
                raise e
                
            return {"status": "success"}
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Error response: {e.response.text}")
            raise e
            
    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Error response: {e.response.text}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
