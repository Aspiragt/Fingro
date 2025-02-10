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

def get_response_for_state(user_id: str, message: str) -> str:
    """
    Determina la respuesta basada en el estado del usuario y su mensaje
    """
    message = message.lower().strip()
    state = user_states.get(user_id, "initial")
    
    if state == "initial":
        if "hola" in message or message == "1":
            user_states[user_id] = "asked_crop"
            return ("¡Hola! 🌱 Bienvenido a Fingro.\n\n"
                   "¿Qué cultivo te gustaría analizar?\n\n"
                   "1. Maíz 🌽\n"
                   "2. Frijol 🫘\n"
                   "3. Café ☕\n"
                   "4. Otro cultivo")
        
        return ("¡Hola! 🌱 Soy el asistente de Fingro.\n\n"
                "¿Te gustaría saber cuánto podrías ganar con tu cosecha?\n\n"
                "Escribe 1 o 'hola' para comenzar")

    elif state == "asked_crop":
        crops = {
            "1": "Maíz 🌽",
            "2": "Frijol 🫘",
            "3": "Café ☕",
            "4": "Otro cultivo"
        }
        
        if message in crops:
            user_states[user_id] = "asked_area"
            selected_crop = crops[message]
            return (f"Has seleccionado: {selected_crop}\n\n"
                   f"¿Cuántas hectáreas o cuerdas tienes sembradas de {selected_crop}?\n\n"
                   "Por favor, escribe el número y especifica si son hectáreas o cuerdas.")
        
        return ("Por favor, selecciona una opción válida:\n\n"
                "1. Maíz 🌽\n"
                "2. Frijol 🫘\n"
                "3. Café ☕\n"
                "4. Otro cultivo")

    elif state == "asked_area":
        # Reiniciamos el estado para una nueva consulta
        user_states[user_id] = "initial"
        return ("¡Gracias por la información! 📊\n\n"
                "Basado en los datos proporcionados, te ayudaré a:\n"
                "✅ Calcular tu rendimiento esperado\n"
                "✅ Estimar tus costos de producción\n"
                "✅ Proyectar tus ganancias potenciales\n\n"
                "¿Te gustaría hacer otra consulta? Escribe 'hola' o '1' para comenzar de nuevo.")

    return "Lo siento, no entendí tu mensaje. Escribe 'hola' o '1' para comenzar."

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint para recibir mensajes de WhatsApp
    """
    try:
        data = await request.json()
        print(f"Datos recibidos en webhook POST: {json.dumps(data, indent=2)}")
        
        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            if 'messages' in value:
                message = value['messages'][0]
                from_number = message['from']
                message_body = message.get('text', {}).get('body', '')
                
                print(f"\nMensaje recibido de {from_number}: {message_body}")
                
                # Obtener respuesta basada en el estado
                response_message = get_response_for_state(from_number, message_body)
                
                try:
                    response = whatsapp.send_text_message(
                        to_number=from_number,
                        message=response_message
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
