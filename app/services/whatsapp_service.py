from typing import Optional, Dict, Any
import os
import json
import httpx
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.user_service import UserService

class WhatsAppCloudAPI:
    def __init__(self):
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.api_version = 'v17.0'
        self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
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
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    self.api_url,
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                print(f"\nAPI Response: {response.text}")
                return response.json()
                
        except Exception as e:
            print(f"\nError sending message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response error: {e.response.text}")
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
            conversation = await self.conversation_service.get_active_conversation(from_number)
            if not conversation:
                print("\n[2] No hay conversación activa, creando nueva...")
                conversation = await self.conversation_service.create_conversation(from_number)
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
        message = message.lower().strip()
        
        print(f"Estado actual: {state}")
        print(f"Mensaje recibido: {message}")
        print(f"Contexto: {json.dumps(context, indent=2)}")
        
        if state == 'initial':
            print("\nVerificando condiciones iniciales:")
            greetings = ['hola', 'hello', 'hi', '1', 'buenos dias', 'buenas']
            
            print(f"Saludos válidos: {greetings}")
            print(f"Mensaje contiene saludo: {any(greeting in message for greeting in greetings)}")
            
            if any(greeting in message for greeting in greetings):
                name = user.name if user.name else ""
                greeting = f", {name}" if name else ""
                
                print("\nActualizando estado a asking_name")
                await self.conversation_service.update_context(
                    conversation.id,
                    {'state': 'asking_name'}
                )
                
                return (f"¡Hola{greeting}! 🚜 Soy Fingro, tu aliado para conseguir financiamiento "
                       f"sin trámites complicados. Te haré unas preguntas rápidas y te diré cuánto "
                       f"podrías ganar con tu cosecha y si calificas para financiamiento. 💰📊\n\n"
                       f"Para empezar, ¿cómo te llamas?")
            
            return ("¡Hola! 🌱 Soy Fingro, tu aliado financiero.\n\n"
                   "¿Te gustaría saber si calificas para financiamiento y cuánto podrías ganar con tu cosecha?\n\n"
                   "Escribe 'hola' o '1' para comenzar")
        
        elif state == 'asking_name':
            # Update user name
            user.name = message.title()  # Capitalize first letter of each word
            await self.user_service.update_user(user.id, {'name': user.name})
            
            await self.conversation_service.update_context(
                conversation.id,
                {'state': 'asking_location'}
            )
            
            return (f"Gracias, {user.name}. Ahora dime, ¿en qué país y "
                   f"departamento/villa/pueblo vives?")
        
        elif state == 'asking_location':
            # Update user location
            location_parts = message.split(',')
            if len(location_parts) >= 2:
                country = location_parts[0].strip().title()
                location = location_parts[1].strip().title()
            else:
                country = "Guatemala"  # Default country
                location = message.strip().title()
            
            await self.user_service.update_user(
                user.id,
                {
                    'country': country,
                    'location': location
                }
            )
            
            await self.conversation_service.update_context(
                conversation.id,
                {'state': 'asking_land_ownership'}
            )
            
            return (f"¡Perfecto! Esto nos ayudará a calcular mejor tu financiamiento. "
                   f"Ahora dime, ¿tienes terrenos propios o alquilados?")
        
        elif state == 'asking_land_ownership':
            ownership = 'propio' if 'propi' in message else 'alquilado' if 'alquil' in message else 'mixto'
            
            await self.user_service.update_user(
                user.id,
                {'land_ownership': ownership}
            )
            
            await self.conversation_service.update_context(
                conversation.id,
                {'state': 'asking_crop'}
            )
            
            return ("¡Gracias por la información! Ahora cuéntame, "
                   "¿qué cultivas actualmente?")
        
        return "Lo siento, no entendí tu mensaje. Escribe 'hola' o '1' para comenzar."
