from typing import Optional, Dict, List
from datetime import datetime
import uuid
from app.database.firebase import db
from app.models.conversation import Conversation, Message
from app.models.user import User

class ConversationService:
    def __init__(self):
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
    
    async def update_context(self, conversation_id: str, context_updates: Dict):
        """Update the conversation context"""
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
    
    async def end_conversation(self, conversation_id: str):
        """End a conversation"""
        await self.db.update_document(
            'conversations',
            conversation_id,
            {'active': False,
             'updated_at': datetime.now()}
        )
        
        return True
