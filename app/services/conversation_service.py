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
        print(f"\nDEBUG - Creating new conversation for user: {user_id}")
        
        # First, end any existing active conversations
        active_conversations = await self.db.query_collection(
            'conversations',
            'user_id',
            '==',
            user_id
        )
        
        for conv in active_conversations:
            if conv.get('active', False):
                print(f"DEBUG - Ending previous active conversation: {conv.get('id')}")
                await self.db.update_document(
                    'conversations',
                    conv.get('id'),
                    {'active': False}
                )
        
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            messages=[],
            context={
                'state': 'initial',
                'collected_data': {},
                'current_crop': None
            },
            active=True
        )
        
        print(f"DEBUG - New conversation created with ID: {conversation.id}")
        print(f"DEBUG - Initial context: {conversation.context}")
        
        await self.db.add_document('conversations', conversation.model_dump(), conversation.id)
        return conversation
    
    async def get_active_conversation(self, user_id: str) -> Optional[Conversation]:
        """Get the active conversation for a user"""
        print(f"\nDEBUG - Getting active conversation for user: {user_id}")
        
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
            print(f"DEBUG - Found active conversation: {active_conversations[0].id}")
            print(f"DEBUG - Conversation context: {active_conversations[0].context}")
        else:
            print("DEBUG - No active conversation found")
        
        return active_conversations[0] if active_conversations else None
    
    async def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to a conversation"""
        print(f"\nDEBUG - Adding message to conversation {conversation_id}")
        print(f"DEBUG - Role: {role}")
        print(f"DEBUG - Content: {content}")
        
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
        print(f"\nDEBUG - Updating context for conversation {conversation_id}")
        print(f"DEBUG - Updates: {context_updates}")
        
        conv_data = await self.db.get_document('conversations', conversation_id)
        if not conv_data:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = Conversation(**conv_data)
        conversation.context.update(context_updates)
        conversation.updated_at = datetime.now()
        
        print(f"DEBUG - New context: {conversation.context}")
        
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
