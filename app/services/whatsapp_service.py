import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime
import uuid
from app.database.firebase import db
from app.services.conversation_service import ConversationService
from app.models.user import User

load_dotenv()

class WhatsAppCloudAPI:
    def __init__(self):
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.api_version = 'v21.0'
        self.api_url = f'https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages'
        self.conversation_service = ConversationService()
        self.db = db
        
    async def get_or_create_user(self, phone_number: str) -> User:
        """Get existing user or create a new one"""
        users = await self.db.query_collection('users', 'phone_number', '==', phone_number)
        
        if users:
            return User(**users[0])
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await self.db.add_document('users', user.model_dump(), user.id)
        return user
    
    async def process_message(self, from_number: str, message_body: str) -> str:
        """Process incoming message and return response"""
        # Get or create user
        user = await self.get_or_create_user(from_number)
        
        # Get active conversation or create new one
        conversation = await self.conversation_service.get_active_conversation(user.id)
        if not conversation:
            conversation = await self.conversation_service.create_conversation(user.id)
        
        # Add user message to conversation
        await self.conversation_service.add_message(
            conversation.id,
            'user',
            message_body
        )
        
        # Process message based on context
        response = await self.get_response_based_on_context(conversation, message_body)
        
        # Add bot response to conversation
        await self.conversation_service.add_message(
            conversation.id,
            'assistant',
            response
        )
        
        return response
    
    async def get_response_based_on_context(self, conversation, message: str) -> str:
        """Generate response based on conversation context"""
        context = conversation.context
        state = context.get('state', 'initial')
        message = message.lower().strip()
        
        if state == 'initial':
            if 'hola' in message or message == '1':
                await self.conversation_service.update_context(
                    conversation.id,
                    {'state': 'asking_crop'}
                )
                return ("¡Hola! 🌱 Bienvenido a Fingro.\n\n"
                       "Me gustaría ayudarte a analizar tu cultivo. "
                       "¿Qué cultivo tienes o te gustaría sembrar?\n\n"
                       "Puedes decirme cualquier cultivo que tengas en mente.")
            
            return ("¡Hola! 🌱 Soy el asistente de Fingro.\n\n"
                    "¿Te gustaría saber cuánto podrías ganar con tu cosecha?\n\n"
                    "Escribe 'hola' o '1' para comenzar")
        
        elif state == 'asking_crop':
            # Store the crop name
            await self.conversation_service.update_context(
                conversation.id,
                {
                    'state': 'asking_area',
                    'collected_data': {
                        'crop': message
                    }
                }
            )
            
            return (f"¡Excelente elección! Has seleccionado: {message}\n\n"
                   f"¿Cuántas hectáreas o cuerdas tienes o planeas sembrar de {message}?\n\n"
                   "Por favor, especifica el número y si son hectáreas o cuerdas.")
        
        elif state == 'asking_area':
            # Try to extract number and unit from message
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', message)
            area = float(numbers[0]) if numbers else 0
            unit = 'hectáreas' if 'hectarea' in message or 'hectárea' in message else 'cuerdas'
            
            collected_data = context.get('collected_data', {})
            collected_data.update({
                'area': area,
                'area_unit': unit
            })
            
            # Create crop in database
            crop = {
                'id': str(uuid.uuid4()),
                'name': collected_data['crop'],
                'type': collected_data['crop'],
                'area': area,
                'area_unit': unit,
                'user_id': conversation.user_id,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            await self.db.add_document('crops', crop, crop['id'])
            
            # Update user's crops
            user_data = await self.db.get_document('users', conversation.user_id)
            if user_data:
                user = User(**user_data)
                user.crops.append(crop['id'])
                await self.db.update_document('users', user.id, {'crops': user.crops})
            
            # Reset conversation state
            await self.conversation_service.update_context(
                conversation.id,
                {
                    'state': 'initial',
                    'collected_data': {}
                }
            )
            
            return (f"¡Perfecto! He registrado tu cultivo de {collected_data['crop']} "
                   f"con un área de {area} {unit}.\n\n"
                   "En los próximos días estaré:\n"
                   "✅ Analizando los precios actuales del mercado\n"
                   "✅ Calculando costos estimados de producción\n"
                   "✅ Preparando recomendaciones personalizadas\n\n"
                   "¿Te gustaría registrar otro cultivo? Escribe 'hola' o '1' para comenzar de nuevo.")
        
        return "Lo siento, no entendí tu mensaje. Escribe 'hola' o '1' para comenzar."
        
    def send_template_message(self, to_number: str, template_name: str, language_code: str = "es") -> Dict:
        """Send a template message"""
        to_number = to_number.lstrip('+')
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Server response: {e.response.text}")
            raise e
    
    def send_text_message(self, to_number: str, message: str) -> Dict:
        """Send a text message"""
        to_number = to_number.lstrip('+')
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Server response: {e.response.text}")
            raise e
