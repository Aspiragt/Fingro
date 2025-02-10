from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from app.services.whatsapp_service import WhatsAppCloudAPI
import json
import os
import traceback

load_dotenv()

app = FastAPI(title="Fingro API")
whatsapp = WhatsAppCloudAPI()

# Estado del usuario
user_states = {}

@app.get("/")
async def root():
    return {"message": "Fingro WhatsApp API"}

@app.delete("/users/{phone_number}/data")
async def delete_user_data(phone_number: str):
    """Delete all data for a user"""
    try:
        await whatsapp.user_service.delete_user_data(phone_number)
        return {"status": "success", "message": f"Data deleted for user {phone_number}"}
    except Exception as e:
        print(f"Error deleting user data: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/database/clean")
async def clean_database():
    """Clean all data from the database"""
    try:
        await whatsapp.user_service.db.delete_all_collections()
        return {"status": "success", "message": "Database cleaned successfully"}
    except Exception as e:
        print(f"Error cleaning database: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

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
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint para recibir mensajes de WhatsApp
    """
    try:
        print("\n=== NUEVO MENSAJE RECIBIDO ===")
        
        # 1. Obtener y validar el JSON
        try:
            data = await request.json()
            print(f"[1] Raw webhook data:\n{json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"[1] Error parsing JSON: {str(e)}")
            print(traceback.format_exc())
            return {"status": "error", "detail": "Invalid JSON"}
        
        # 2. Validar estructura básica
        if not isinstance(data, dict):
            print("[2] Data is not a dictionary")
            return {"status": "error", "detail": "Invalid data structure"}
        
        # 3. Extraer entry
        if not data.get('entry'):
            print("[3] No entries found")
            return {"status": "success"}  # WhatsApp puede enviar pings sin entries
            
        entry = data['entry'][0]
        print(f"[3] Entry data:\n{json.dumps(entry, indent=2)}")
        
        # 4. Extraer changes
        if not entry.get('changes'):
            print("[4] No changes found")
            return {"status": "success"}
            
        changes = entry['changes'][0]
        print(f"[4] Changes data:\n{json.dumps(changes, indent=2)}")
        
        # 5. Extraer value
        if not changes.get('value'):
            print("[5] No value found")
            return {"status": "success"}
            
        value = changes['value']
        print(f"[5] Value data:\n{json.dumps(value, indent=2)}")
        
        # 6. Extraer messages
        if not value.get('messages'):
            print("[6] No messages found")
            return {"status": "success"}
            
        message = value['messages'][0]
        print(f"[6] Message data:\n{json.dumps(message, indent=2)}")
        
        # 7. Validar tipo de mensaje
        if message.get('type') != 'text':
            print(f"[7] Message is not text type: {message.get('type')}")
            return {"status": "success"}
        
        # 8. Extraer información del mensaje
        from_number = message['from']
        if not message.get('text', {}).get('body'):
            print("[8] No message body found")
            return {"status": "success"}
            
        message_body = message['text']['body']
        
        print(f"\n[8] Mensaje procesado:")
        print(f"- From: {from_number}")
        print(f"- Body: {message_body}")
        
        # 9. Procesar mensaje
        try:
            print("\n[9] Procesando mensaje con WhatsApp service...")
            response_message = await whatsapp.process_message(from_number, message_body)
            print(f"[9] Respuesta generada: {response_message}")
        except Exception as e:
            print(f"[9] Error processing message: {str(e)}")
            print(traceback.format_exc())
            raise
        
        # 10. Enviar respuesta
        try:
            print("\n[10] Enviando respuesta...")
            response = whatsapp.send_text_message(
                to_number=from_number,
                message=response_message
            )
            print(f"[10] Respuesta enviada exitosamente:\n{json.dumps(response, indent=2)}")
        except Exception as e:
            print(f"[10] Error sending response: {str(e)}")
            print(traceback.format_exc())
            if hasattr(e, 'response'):
                print(f"Response error: {e.response.text}")
            raise
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"\n=== ERROR EN WEBHOOK ===")
        print(str(e))
        print(traceback.format_exc())
        if hasattr(e, 'response'):
            print(f"Response error: {e.response.text}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
