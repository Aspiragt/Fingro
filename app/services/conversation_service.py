from typing import Optional, List, Any
from datetime import datetime
import logging
import uuid
from app.database.firebase import db
from app.models.conversation import Conversation, Message
from app.models.user import User

logger = logging.getLogger(__name__)

class ConversationService:
    """Servicio para manejar conversaciones de WhatsApp"""

    def __init__(self):
        """Inicializa el servicio de conversación"""
        self.flow = ConversationFlow()
        self.whatsapp = WhatsAppService()
        self.db = db
    
    async def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation for a user"""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            messages=[],
            context={
                'state': 'initial',
                'collected_data': {},
                'current_crop': None
            }
        )
        
        await self.db.add_document('conversations', conversation.model_dump(), conversation.id)
        return conversation
    
    async def get_active_conversation(self, user_id: str) -> Optional[Conversation]:
        """Get the active conversation for a user"""
        conversations = await self.db.query_collection(
            'conversations',
            'user_id',
            '==',
            user_id
        )
        
        active_conversations = [
            Conversation(**conv) for conv in conversations 
            if conv.get('active', False)
        ]
        
        return active_conversations[0] if active_conversations else None
    
    async def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to a conversation"""
        message = Message(role=role, content=content)
        
        # Get current conversation
        conv_data = await self.db.get_document('conversations', conversation_id)
        if not conv_data:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = Conversation(**conv_data)
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # Update in database
        await self.db.update_document(
            'conversations',
            conversation_id,
            {'messages': [m.model_dump() for m in conversation.messages],
             'updated_at': conversation.updated_at}
        )
        
        return message
    
    async def update_context(self, conversation_id: str, context_updates: dict):
        """Update the conversation context"""
        try:
            conv_data = await self.db.get_document('conversations', conversation_id)
            if not conv_data:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation = Conversation(**conv_data)
            conversation.context.update(context_updates)
            conversation.updated_at = datetime.now()
            
            await self.db.update_document(
                'conversations',
                conversation_id,
                {'context': conversation.context,
                 'updated_at': conversation.updated_at}
            )
            
            return conversation.context
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
            raise
    
    async def end_conversation(self, conversation_id: str):
        """End a conversation"""
        await self.db.update_document(
            'conversations',
            conversation_id,
            {'active': False,
             'updated_at': datetime.now()}
        )
        
        return True

    async def handle_message(self, phone_number: str, message: str) -> None:
        """
        Maneja un mensaje de WhatsApp
        
        Args:
            phone_number: Número de teléfono del usuario
            message: Mensaje recibido
        """
        try:
            # Normalizar mensaje
            message = message.strip()
            
            # Si es comando especial, procesar
            if message.lower() == 'inicio':
                await self.restart_conversation(phone_number)
                return
                
            if message.lower() == 'ayuda':
                await self.show_help(phone_number)
                return
                
            if message.lower() == 'asesor':
                await self.connect_to_advisor(phone_number)
                return
            
            # Procesar mensaje normal
            await self.flow.process_message(phone_number, message)
            
        except Exception as e:
            logger.error(f"Error en handle_message: {str(e)}")
            await self.whatsapp.send_message(
                phone_number,
                "Lo siento, hubo un error. Por favor escriba 'inicio' para empezar de nuevo."
            )

    async def restart_conversation(self, phone_number: str) -> None:
        """Reinicia la conversación"""
        try:
            # Limpiar datos del usuario
            self.flow.user_data[phone_number] = {'data': {}, 'state': 'start'}
            
            # Enviar mensaje de bienvenida
            welcome = self.flow.start_conversation()
            await self.whatsapp.send_message(phone_number, welcome)
            
        except Exception as e:
            logger.error(f"Error reiniciando conversación: {str(e)}")
            await self.whatsapp.send_message(
                phone_number,
                "Lo siento, hubo un error. Por favor intente de nuevo."
            )

    async def show_help(self, phone_number: str) -> None:
        """Muestra mensaje de ayuda"""
        try:
            # Obtener estado actual
            user_data = self.flow.user_data.get(phone_number, {'data': {}})
            
            # Obtener ayuda contextual
            help_message = self.flow.show_help(user_data)
            await self.whatsapp.send_message(phone_number, help_message)
            
        except Exception as e:
            logger.error(f"Error mostrando ayuda: {str(e)}")
            await self.whatsapp.send_message(
                phone_number,
                "Lo siento, hubo un error. Por favor escriba 'inicio' para empezar de nuevo."
            )

    async def connect_to_advisor(self, phone_number: str) -> None:
        """Conecta con un asesor"""
        try:
            # Obtener datos del usuario
            user_data = self.flow.user_data.get(phone_number, {'data': {}})
            
            # Conectar con asesor
            message = self.flow.connect_to_advisor(user_data)
            await self.whatsapp.send_message(phone_number, message)
            
            # Guardar datos actualizados
            self.flow.user_data[phone_number] = user_data
            
        except Exception as e:
            logger.error(f"Error conectando con asesor: {str(e)}")
            await self.whatsapp.send_message(
                phone_number,
                "Lo siento, hubo un error. Por favor escriba 'inicio' para empezar de nuevo."
            )

# Instancia global
conversation_service = ConversationService()
