from typing import Optional, Dict, List
from datetime import datetime
import uuid
import json
from app.database.firebase import db
from app.models.conversation import Conversation, Message
from app.models.user import User

class ConversationService:
    def __init__(self):
        self.db = db
    
    async def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation for a user"""
        print(f"\n=== CREANDO NUEVA CONVERSACIÓN ===")
        print(f"Usuario ID: {user_id}")
        
        # First, end any existing active conversations
        active_conversations = await self.db.query_collection(
            'conversations',
            'user_id',
            '==',
            user_id
        )
        
        for conv in active_conversations:
            if conv.get('active', False):
                print(f"Finalizando conversación activa anterior: {conv.get('id')}")
                await self.db.update_document(
                    'conversations',
                    conv.get('id'),
                    {'active': False}
                )
        
        # Create new conversation
        conversation_id = str(uuid.uuid4())
        now = datetime.now()
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=[],
            context={
                'state': 'initial',
                'collected_data': {}
            },
            active=True,
            created_at=now,
            updated_at=now
        )
        
        print(f"Nueva conversación creada:")
        print(f"ID: {conversation.id}")
        print(f"Estado inicial: {conversation.context.get('state')}")
        print(f"Contexto: {json.dumps(conversation.context, indent=2)}")
        
        # Save to database
        await self.db.add_document(
            'conversations', 
            conversation.model_dump(), 
            conversation.id
        )
        
        # Update user's active conversation
        await self.db.update_document(
            'users',
            user_id,
            {'active_conversation': conversation.id}
        )
        
        return conversation
    
    async def get_active_conversation(self, user_id: str) -> Optional[Conversation]:
        """Get the active conversation for a user"""
        print(f"\n=== BUSCANDO CONVERSACIÓN ACTIVA ===")
        print(f"Usuario ID: {user_id}")
        
        # First try to get user's active conversation ID
        user_data = await self.db.query_collection('users', 'id', '==', user_id)
        if user_data and user_data[0].get('active_conversation'):
            active_conv_id = user_data[0]['active_conversation']
            conv_data = await self.db.get_document('conversations', active_conv_id)
            if conv_data and conv_data.get('active', False):
                conversation = Conversation(**conv_data)
                print(f"Conversación activa encontrada por ID de usuario:")
                print(f"ID: {conversation.id}")
                print(f"Estado: {conversation.context.get('state')}")
                print(f"Contexto: {json.dumps(conversation.context, indent=2)}")
                return conversation
        
        # If not found by active_conversation, try to find by query
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
        
        if active_conversations:
            conversation = active_conversations[0]
            print(f"Conversación activa encontrada por query:")
            print(f"ID: {conversation.id}")
            print(f"Estado: {conversation.context.get('state')}")
            print(f"Contexto: {json.dumps(conversation.context, indent=2)}")
            
            # Update user's active_conversation field
            await self.db.update_document(
                'users',
                user_id,
                {'active_conversation': conversation.id}
            )
            
            return conversation
        
        print("No se encontró conversación activa")
        return None
    
    async def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to a conversation"""
        print(f"\n=== AGREGANDO MENSAJE ===")
        print(f"Conversación ID: {conversation_id}")
        print(f"Rol: {role}")
        print(f"Contenido: {content}")
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        
        # Get current conversation
        conv_data = await self.db.get_document('conversations', conversation_id)
        if not conv_data:
            print(f"Error: Conversación {conversation_id} no encontrada")
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = Conversation(**conv_data)
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # Update in database
        await self.db.update_document(
            'conversations',
            conversation_id,
            {
                'messages': [m.model_dump() for m in conversation.messages],
                'updated_at': conversation.updated_at
            }
        )
        
        print("Mensaje agregado exitosamente")
        return message
    
    async def update_context(self, conversation_id: str, context_updates: Dict):
        """Update the conversation context"""
        print(f"\n=== ACTUALIZANDO CONTEXTO ===")
        print(f"Conversación ID: {conversation_id}")
        print(f"Actualizaciones: {json.dumps(context_updates, indent=2)}")
        
        conv_data = await self.db.get_document('conversations', conversation_id)
        if not conv_data:
            print(f"Error: Conversación {conversation_id} no encontrada")
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = Conversation(**conv_data)
        old_context = conversation.context.copy()
        conversation.context.update(context_updates)
        conversation.updated_at = datetime.now()
        
        print(f"Contexto anterior: {json.dumps(old_context, indent=2)}")
        print(f"Nuevo contexto: {json.dumps(conversation.context, indent=2)}")
        
        # Update in database
        await self.db.update_document(
            'conversations',
            conversation_id,
            {
                'context': conversation.context,
                'updated_at': conversation.updated_at
            }
        )
        
        print("Contexto actualizado exitosamente")
        return conversation.context
    
    async def end_conversation(self, conversation_id: str):
        """End a conversation"""
        print(f"\n=== FINALIZANDO CONVERSACIÓN ===")
        print(f"Conversación ID: {conversation_id}")
        
        # Get conversation to get user_id
        conv_data = await self.db.get_document('conversations', conversation_id)
        if not conv_data:
            print(f"Error: Conversación {conversation_id} no encontrada")
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = Conversation(**conv_data)
        
        # Update conversation status
        await self.db.update_document(
            'conversations',
            conversation_id,
            {
                'active': False,
                'updated_at': datetime.now()
            }
        )
        
        # Clear user's active conversation
        await self.db.update_document(
            'users',
            conversation.user_id,
            {'active_conversation': None}
        )
        
        print("Conversación finalizada exitosamente")
        return True
