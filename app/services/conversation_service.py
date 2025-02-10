from typing import Optional, List
from datetime import datetime
import uuid
import json
from app.models.conversation import Conversation, Message
from app.database.firebase import db

class ConversationService:
    def __init__(self):
        self.db = db
    
    async def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation"""
        try:
            conversation = Conversation(
                id='',  # Se actualizará después
                user_id=user_id,
                messages=[],
                context={'state': 'initial'},  # Inicializar con estado initial
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Guardar en Firebase
            conv_dict = conversation.model_dump()
            doc_id = await self.db.add_document('conversations', conv_dict)
            
            # Actualizar ID
            conversation.id = doc_id
            await self.db.update_document('conversations', doc_id, {'id': doc_id})
            
            print(f"Nueva conversación creada: {conversation.model_dump_json(indent=2)}")
            return conversation
            
        except Exception as e:
            print(f"Error en create_conversation: {str(e)}")
            raise e
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        try:
            conv_data = await self.db.get_document('conversations', conversation_id)
            if not conv_data:
                return None
            
            # Convertir strings ISO a datetime
            if isinstance(conv_data.get('created_at'), str):
                conv_data['created_at'] = datetime.fromisoformat(conv_data['created_at'])
            if isinstance(conv_data.get('updated_at'), str):
                conv_data['updated_at'] = datetime.fromisoformat(conv_data['updated_at'])
            
            # Convertir mensajes
            messages = []
            for msg_data in conv_data.get('messages', []):
                if isinstance(msg_data.get('timestamp'), str):
                    msg_data['timestamp'] = datetime.fromisoformat(msg_data['timestamp'])
                messages.append(Message(**msg_data))
            conv_data['messages'] = messages
            
            return Conversation(**conv_data)
            
        except Exception as e:
            print(f"Error en get_conversation: {str(e)}")
            raise e
    
    async def get_active_conversation(self, user_id: str) -> Optional[Conversation]:
        """Get the active conversation for a user"""
        try:
            print("\n=== BUSCANDO CONVERSACIÓN ACTIVA ===")
            print(f"Usuario ID: {user_id}")
            
            # 1. Buscar conversaciones del usuario
            convs = await self.db.query_collection(
                'conversations',
                'user_id',
                '==',
                user_id
            )
            
            # 2. Filtrar por activas
            active_convs = [conv for conv in convs if conv.get('active', False)]
            if not active_convs:
                return None
            
            conv_data = active_convs[0]
            
            # 3. Convertir strings ISO a datetime
            if isinstance(conv_data.get('created_at'), str):
                conv_data['created_at'] = datetime.fromisoformat(conv_data['created_at'])
            if isinstance(conv_data.get('updated_at'), str):
                conv_data['updated_at'] = datetime.fromisoformat(conv_data['updated_at'])
            
            # 4. Convertir mensajes
            messages = []
            for msg_data in conv_data.get('messages', []):
                if isinstance(msg_data.get('timestamp'), str):
                    msg_data['timestamp'] = datetime.fromisoformat(msg_data['timestamp'])
                messages.append(Message(**msg_data))
            conv_data['messages'] = messages
            
            # 5. Asegurar que el contexto tenga un estado válido
            if not conv_data.get('context'):
                conv_data['context'] = {'state': 'initial'}
            elif not conv_data['context'].get('state'):
                conv_data['context']['state'] = 'initial'
            
            conversation = Conversation(**conv_data)
            
            print(f"Conversación activa encontrada:")
            print(f"ID: {conversation.id}")
            print(f"Estado: {conversation.context.get('state')}")
            print(f"Contexto: {json.dumps(conversation.context, indent=2)}")
            
            return conversation
            
        except Exception as e:
            print(f"Error en get_active_conversation: {str(e)}")
            raise e
    
    async def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Add a message to a conversation"""
        try:
            # Obtener conversación
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Crear mensaje
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.now()
            )
            
            # Agregar mensaje y actualizar
            conversation.messages.append(message)
            conversation.updated_at = datetime.now()
            
            # Guardar en Firebase
            conv_dict = conversation.model_dump()
            await self.db.update_document('conversations', conversation_id, conv_dict)
            
            return True
            
        except Exception as e:
            print(f"Error en add_message: {str(e)}")
            raise e
    
    async def update_conversation_context(self, conversation_id: str, context: dict) -> bool:
        """Update conversation context"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Actualizar el contexto existente en lugar de sobrescribirlo
            conversation.context.update(context)
            conversation.updated_at = datetime.now()
            
            conv_dict = conversation.model_dump()
            await self.db.update_document('conversations', conversation_id, conv_dict)
            
            print(f"Contexto actualizado: {conversation.context}")
            return True
            
        except Exception as e:
            print(f"Error en update_conversation_context: {str(e)}")
            raise e
    
    async def reset_conversation(self, conversation_id: str) -> bool:
        """Reset a conversation to initial state"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Resetear el contexto
            conversation.context = {'state': 'initial'}
            conversation.updated_at = datetime.now()
            
            conv_dict = conversation.model_dump()
            await self.db.update_document('conversations', conversation_id, conv_dict)
            
            print(f"Conversación reseteada: {conversation.model_dump_json(indent=2)}")
            return True
            
        except Exception as e:
            print(f"Error en reset_conversation: {str(e)}")
            raise e
    
    async def close_conversation(self, conversation_id: str) -> bool:
        """Close a conversation"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation.active = False
            conversation.updated_at = datetime.now()
            
            conv_dict = conversation.model_dump()
            await self.db.update_document('conversations', conversation_id, conv_dict)
            
            return True
            
        except Exception as e:
            print(f"Error en close_conversation: {str(e)}")
            raise e
