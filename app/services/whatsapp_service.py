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
        response = await self.get_response_based_on_context(conversation, message_body, user)
        
        # Add bot response to conversation
        await self.conversation_service.add_message(
            conversation.id,
            'assistant',
            response
        )
        
        return response
    
    async def get_response_based_on_context(self, conversation, message: str, user: User) -> str:
        """Generate response based on conversation context"""
        context = conversation.context
        state = context.get('state', 'initial')
        message = message.lower().strip()
        
        print(f"\nDEBUG - Current state: {state}")
        print(f"DEBUG - Message received: {message}")
        print(f"DEBUG - Context: {context}")
        
        if state == 'initial':
            print(f"DEBUG - Checking initial state conditions")
            print(f"DEBUG - 'hola' in message: {'hola' in message}")
            print(f"DEBUG - message == '1': {message == '1'}")
            
            if 'hola' in message or message == '1':
                name = user.name if user.name else ""
                greeting = f", {name}" if name else ""
                
                print(f"DEBUG - Updating state to asking_name")
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
            await self.db.update_document('users', user.id, {'name': user.name})
            
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
            
            await self.db.update_document(
                'users', 
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
            
            await self.db.update_document(
                'users',
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
