from typing import Optional, Dict, Any
import os
import json
import httpx
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.user_service import UserService

class WhatsAppCloudAPI:
    def __init__(self):
        print("\n=== INICIALIZANDO WHATSAPP API ===")
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.api_version = 'v17.0'
        self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        
        print(f"Phone Number ID: {self.phone_number_id}")
        print(f"Access Token: {'*' * 20}{self.access_token[-4:] if self.access_token else 'None'}")
        print(f"API Version: {self.api_version}")
        print(f"API URL: {self.api_url}")
        
        if not self.phone_number_id or not self.access_token:
            print("ERROR: Missing required environment variables")
            print(f"WHATSAPP_PHONE_NUMBER_ID: {'Present' if self.phone_number_id else 'Missing'}")
            print(f"WHATSAPP_ACCESS_TOKEN: {'Present' if self.access_token else 'Missing'}")
            raise ValueError("Missing required WhatsApp API configuration")
        
        self.conversation_service = ConversationService()
        self.user_service = UserService()

    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a text message to a WhatsApp number"""
        print(f"\n=== ENVIANDO MENSAJE ===")
        print(f"To: {to_number}")
        print(f"Message: {message}")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }
        
        print(f"\nAPI Request:")
        print(f"URL: {self.api_url}")
        print(f"Headers: {json.dumps({k: '***' if k == 'Authorization' else v for k, v in headers.items()}, indent=2)}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                print(f"\nAPI Response Status: {response.status_code}")
                print(f"API Response Headers: {dict(response.headers)}")
                print(f"API Response Body: {response.text}")
                
                try:
                    response_json = response.json()
                    print(f"API Response JSON: {json.dumps(response_json, indent=2)}")
                except json.JSONDecodeError:
                    print("Response is not JSON")
                
                if response.status_code == 401:
                    print("\nERROR 401: Unauthorized")
                    print("This usually means:")
                    print("1. The access token is invalid")
                    print("2. The access token has expired")
                    print("3. The access token doesn't have the required permissions")
                    raise ValueError("WhatsApp API authentication failed")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            print(f"\nHTTP Error: {str(e)}")
            print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            raise
        except httpx.RequestError as e:
            print(f"\nRequest Error: {str(e)}")
            raise
        except Exception as e:
            print(f"\nUnexpected Error: {str(e)}")
            raise

    async def process_message(self, from_number: str, message: str) -> str:
        """Process an incoming message and return the appropriate response"""
        print(f"\n=== PROCESANDO MENSAJE ===")
        print(f"From: {from_number}")
        print(f"Message: {message}")
        
        try:
            # 1. Obtener o crear usuario
            user = await self.user_service.get_or_create_user(from_number)
            print(f"\n[1] Usuario: {user.model_dump_json(indent=2)}")
            
            # 2. Obtener o crear conversación
            conversation = await self.conversation_service.get_active_conversation(user.id)
            if not conversation:
                print("\n[2] No hay conversación activa, creando nueva...")
                conversation = await self.conversation_service.create_conversation(user.id)
            print(f"\n[2] Conversación: {conversation.model_dump_json(indent=2)}")
            
            # 3. Guardar mensaje del usuario
            await self.conversation_service.add_message(conversation.id, "user", message)
            print("\n[3] Mensaje del usuario guardado")
            
            # 4. Generar respuesta basada en contexto
            response = await self.get_response_based_on_context(conversation, message, user)
            print(f"\n[4] Respuesta generada: {response}")
            
            # 5. Guardar respuesta del bot
            await self.conversation_service.add_message(conversation.id, "bot", response)
            print("\n[5] Respuesta del bot guardada")
            
            return response
            
        except Exception as e:
            print(f"\nError processing message: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return "Lo siento, ha ocurrido un error. Por favor, intenta nuevamente."

    async def get_response_based_on_context(self, conversation, message: str, user: User) -> str:
        """Generate response based on conversation context"""
        print(f"\n=== GENERANDO RESPUESTA ===")
        
        context = conversation.context
        state = context.get('state', 'initial')
        original_message = message
        message = message.lower().strip()
        
        print(f"Estado actual: {state}")
        print(f"Mensaje original: {original_message}")
        print(f"Mensaje procesado: {message}")
        print(f"Contexto: {json.dumps(context, indent=2)}")
        
        if state == 'initial':
            print("\nVerificando condiciones iniciales:")
            greetings = ['hola', 'hello', 'hi', '1', 'buenos dias', 'buenas']
            
            print(f"Saludos válidos: {greetings}")
            print(f"Mensaje contiene saludo: {any(greeting in message for greeting in greetings)}")
            
            # Verificar cada saludo individualmente para depuración
            for greeting in greetings:
                print(f"- '{greeting}' in '{message}': {greeting in message}")
            
            if any(greeting in message for greeting in greetings):
                name = user.name if user.name else ""
                greeting = f", {name}" if name else ""
                
                print("\nActualizando estado a asking_name")
                await self.conversation_service.update_conversation_context(
                    conversation.id,
                    {'state': 'asking_name'}
                )
                
                return (f"¡Hola{greeting}! 🚜 Soy Fingro, tu aliado para conseguir financiamiento "
                       f"sin trámites complicados. Te haré unas preguntas rápidas y te diré cuánto "
                       f"podrías ganar con tu cosecha y si calificas para financiamiento. 💰📊\n\n"
                       f"Para empezar, ¿cómo te llamas?")
            
            print("\nNo se detectó un saludo válido")
            return ("¡Hola! 🌱 Soy Fingro, tu aliado financiero.\n\n"
                   "¿Te gustaría saber si calificas para financiamiento y cuánto podrías ganar con tu cosecha?\n\n"
                   "Escribe 'hola' o '1' para comenzar")
        
        elif state == 'asking_name':
            print("\nProcesando nombre del usuario")
            # Update user name
            user.name = message.title()  # Capitalize first letter of each word
            await self.user_service.update_user(user)
            
            print(f"Nombre guardado: {user.name}")
            await self.conversation_service.update_conversation_context(
                conversation.id,
                {'state': 'asking_location'}
            )
            
            return (f"¡Gracias {user.name}! 🤝\n\n"
                   f"¿En qué departamento te encuentras?")
        
        elif state == 'asking_location':
            print("\nProcesando ubicación del usuario")
            # Update user location
            if ',' in message:
                country, location = [part.strip() for part in message.split(',')]
            else:
                country = "Guatemala"  # Default country
                location = message.strip().title()
            
            print(f"País: {country}")
            print(f"Ubicación: {location}")
            
            user.country = country
            user.location = location
            await self.user_service.update_user(user)
            
            await self.conversation_service.update_conversation_context(
                conversation.id,
                {'state': 'asking_land_ownership'}
            )
            
            return ("¡Excelente! 🌎\n\n"
                   "¿Los terrenos donde cultivas son propios o alquilados?")
        
        elif state == 'asking_land_ownership':
            print("\nProcesando propiedad de terrenos")
            ownership = 'propio' if 'propi' in message else 'alquilado' if 'alquil' in message else 'mixto'
            
            print(f"Tipo de propiedad detectado: {ownership}")
            
            user.land_ownership = ownership
            await self.user_service.update_user(user)
            
            await self.conversation_service.update_conversation_context(
                conversation.id,
                {'state': 'asking_crop'}
            )
            
            return ("¡Perfecto! 🌱\n\n"
                   "¿qué cultivas actualmente?")
        
        print("\nNo se encontró un estado válido")
        return "Lo siento, no entendí tu mensaje. Escribe 'hola' o '1' para comenzar."
