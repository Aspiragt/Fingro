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
        print(f"\n{'='*50}")
        print(f"PROCESANDO MENSAJE")
        print(f"{'='*50}")
        print(f"De: {from_number}")
        print(f"Mensaje: {message}")
        
        try:
            # 1. Obtener o crear usuario
            print(f"\n{'>'*20} PASO 1: Usuario {'<'*20}")
            user = await self.user_service.get_or_create_user(from_number)
            print(f"Usuario: {user.model_dump_json(indent=2)}")
            
            # 2. Obtener o crear conversación
            print(f"\n{'>'*20} PASO 2: Conversación {'<'*20}")
            conversation = await self.conversation_service.get_active_conversation(user.id)
            if not conversation:
                print("No hay conversación activa, creando nueva...")
                conversation = await self.conversation_service.create_conversation(user.id)
            print(f"Conversación: {conversation.model_dump_json(indent=2)}")
            
            # 3. Guardar mensaje del usuario
            print(f"\n{'>'*20} PASO 3: Guardar Mensaje {'<'*20}")
            await self.conversation_service.add_message(conversation.id, "user", message)
            print("Mensaje guardado")
            
            # 4. Generar respuesta basada en contexto
            print(f"\n{'>'*20} PASO 4: Generar Respuesta {'<'*20}")
            response = await self.get_response_based_on_context(conversation, message, user)
            print(f"Respuesta: {response}")
            
            # 5. Guardar respuesta del bot
            print(f"\n{'>'*20} PASO 5: Guardar Respuesta {'<'*20}")
            await self.conversation_service.add_message(conversation.id, "bot", response)
            print("Respuesta guardada")
            
            print(f"\n{'='*50}")
            print(f"MENSAJE PROCESADO EXITOSAMENTE")
            print(f"{'='*50}\n")
            
            return response
            
        except Exception as e:
            print(f"\n{'!'*50}")
            print(f"ERROR PROCESANDO MENSAJE")
            print(f"{'!'*50}")
            print(f"Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return "Lo siento, ha ocurrido un error. Por favor, intenta nuevamente."

    async def get_response_based_on_context(self, conversation, message: str, user: User) -> str:
        """Generate response based on conversation context"""
        try:
            print(f"\n=== GENERANDO RESPUESTA BASADA EN CONTEXTO ===")
            print(f"Estado actual: {conversation.context.get('state', 'unknown')}")
            print(f"Mensaje: {message}")
            
            # Obtener estado actual y procesar mensaje
            state = conversation.context.get('state', 'initial')
            message = message.lower().strip()
            
            # Inicializar respuestas si no existen
            if 'responses' not in conversation.context:
                conversation.context['responses'] = {}
            
            print(f"\nProcesando estado: {state}")
            print(f"Respuestas anteriores: {json.dumps(conversation.context.get('responses', {}), indent=2)}")
            
            if state == 'initial':
                greetings = ['hola', 'hello', 'hi', '1', 'buenos dias', 'buenas']
                if any(greeting in message for greeting in greetings):
                    # Resetear conversación si es necesario
                    if conversation.context.get('state') != 'initial':
                        await self.conversation_service.reset_conversation(conversation.id)
                    
                    # Actualizar contexto
                    await self.conversation_service.update_conversation_context(
                        conversation.id,
                        {
                            'state': 'welcome',
                            'responses': {'greeting': message}
                        }
                    )
                    
                    name = user.name if user.name else ""
                    greeting = f", {name}" if name else ""
                    return (f"¡Hola{greeting}! 🌱\n\n"
                           f"Soy *Fingro*, tu asistente financiero inteligente. "
                           f"Te ayudaré a conseguir el financiamiento que necesitas para tu cosecha, "
                           f"de manera rápida y sin complicaciones.\n\n"
                           f"¿Te gustaría saber:\n"
                           f"✨ Cuánto podrías ganar con tu cosecha?\n"
                           f"💰 Si calificas para financiamiento?\n"
                           f"📊 Qué opciones de crédito tenemos para ti?\n\n"
                           f"Responde *SI* para comenzar. 🚀")
                
                return ("¡Hola! 🌱\n\n"
                       "Soy *Fingro*, tu aliado financiero para el campo.\n\n"
                       "¿Te gustaría conocer las opciones de financiamiento que tenemos para tu cosecha? Salúdame para comenzar. 👋")
            
            elif state == 'welcome':
                confirmations = ['si', 'sí', 'yes', 'ok', 'dale', 'va', 'empezar', 'comenzar', 'claro']
                if any(confirm in message for confirm in confirmations):
                    # Guardar respuesta y actualizar estado
                    responses = conversation.context.get('responses', {})
                    responses['confirmation'] = message
                    
                    await self.conversation_service.update_conversation_context(
                        conversation.id,
                        {
                            'state': 'asking_name',
                            'responses': responses
                        }
                    )
                    return ("¡Perfecto! 🌟 Para empezar, ¿podrías decirme tu nombre?")
                else:
                    return ("Para comenzar el proceso, por favor responde *SI*.\n\n"
                           "Si no deseas continuar, puedes escribir 'salir' en cualquier momento.")

            elif state == 'asking_name':
                # Guardar nombre en usuario y en contexto
                user.name = message.title()
                await self.user_service.update_user(user)
                
                responses = conversation.context.get('responses', {})
                responses['name'] = user.name
                
                await self.conversation_service.update_conversation_context(
                    conversation.id,
                    {
                        'state': 'asking_location',
                        'responses': responses
                    }
                )
                
                return (f"¡Gracias {user.name}! 🤝\n\n"
                       f"¿En qué departamento te encuentras?")

            elif state == 'asking_location':
                # Procesar ubicación
                if ',' in message:
                    country, location = [part.strip() for part in message.split(',')]
                else:
                    country = "Guatemala"
                    location = message.strip().title()
                
                # Actualizar usuario
                user.country = country
                user.location = location
                await self.user_service.update_user(user)
                
                # Guardar en contexto
                responses = conversation.context.get('responses', {})
                responses['location'] = {
                    'country': country,
                    'department': location
                }
                
                await self.conversation_service.update_conversation_context(
                    conversation.id,
                    {
                        'state': 'asking_land_ownership',
                        'responses': responses
                    }
                )
                
                return ("¡Excelente! 🌎\n\n"
                       "¿Los terrenos donde cultivas son propios o alquilados?")

            elif state == 'asking_land_ownership':
                # Determinar tipo de propiedad
                ownership = 'propio' if 'propi' in message else 'alquilado' if 'alquil' in message else 'mixto'
                
                # Actualizar usuario
                user.land_ownership = ownership
                await self.user_service.update_user(user)
                
                # Guardar en contexto
                responses = conversation.context.get('responses', {})
                responses['land_ownership'] = ownership
                
                await self.conversation_service.update_conversation_context(
                    conversation.id,
                    {
                        'state': 'asking_crop',
                        'responses': responses
                    }
                )
                
                return ("¡Perfecto! 🌱\n\n"
                       "¿qué cultivas actualmente?")

            elif state == 'asking_crop':
                # Guardar cultivo
                responses = conversation.context.get('responses', {})
                responses['crop'] = message.strip()
                
                # Actualizar usuario
                user.crops.append(message.strip())
                await self.user_service.update_user(user)
                
                await self.conversation_service.update_conversation_context(
                    conversation.id,
                    {
                        'state': 'finished',
                        'responses': responses
                    }
                )
                
                return (f"¡Excelente {user.name}! 🎉\n\n"
                       f"He guardado toda tu información. Pronto un asesor se pondrá en contacto contigo "
                       f"para discutir las opciones de financiamiento disponibles para tu cultivo de {message.strip()}.\n\n"
                       f"Si tienes alguna pregunta adicional, no dudes en escribirme.")
            
            print("\nNo se encontró un estado válido")
            return "Lo siento, no entendí tu mensaje. Escribe 'hola' o '1' para comenzar."

        except Exception as e:
            print(f"\n{'!'*50}")
            print(f"ERROR GENERANDO RESPUESTA")
            print(f"{'!'*50}")
            print(f"Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return "Lo siento, ha ocurrido un error. Por favor, intenta nuevamente."
