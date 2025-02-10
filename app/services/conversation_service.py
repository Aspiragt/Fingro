from typing import Optional, List, Dict
from datetime import datetime
import uuid
import json
from app.models.conversation import Conversation, Message
from app.database.firebase import db

class ConversationService:
    def __init__(self):
        self.db = db
    
    async def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation for a user"""
        try:
            print(f"\n=== CREANDO NUEVA CONVERSACIÓN ===")
            print(f"Usuario ID: {user_id}")
            
            # Primero cerrar cualquier conversación activa existente
            active_conv = await self.get_active_conversation(user_id)
            if active_conv:
                print(f"Cerrando conversación activa: {active_conv.id}")
                await self.close_conversation(active_conv.id)
            
            # Generar ID único
            conversation_id = str(uuid.uuid4())
            
            # Crear datos de la conversación
            conversation_data = {
                'id': conversation_id,
                'user_id': user_id,
                'context': {'state': 'initial'},
                'messages': [],
                'active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Guardar en base de datos usando el ID generado
            saved_data = await self.db.add_document('conversations', conversation_data, conversation_id)
            
            # Convertir a modelo
            conversation = Conversation(**saved_data)
            print(f"Nueva conversación creada: {conversation.model_dump_json(indent=2)}")
            return conversation
            
        except Exception as e:
            print(f"Error en create_conversation: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise e
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        try:
            print(f"\n=== BUSCANDO CONVERSACIÓN ===")
            print(f"ID: {conversation_id}")
            
            # Obtener conversación
            conv = await self.db.get_document('conversations', conversation_id)
            if not conv:
                print("Conversación no encontrada")
                return None
            
            # Convertir timestamps
            if isinstance(conv.get('created_at'), str):
                conv['created_at'] = datetime.fromisoformat(conv['created_at'])
            if isinstance(conv.get('updated_at'), str):
                conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
            
            # Convertir mensajes
            messages = []
            for msg in conv.get('messages', []):
                if isinstance(msg.get('timestamp'), str):
                    msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
                messages.append(Message(**msg))
            conv['messages'] = messages
            
            # Asegurar que el contexto tenga un estado válido
            if not conv.get('context'):
                conv['context'] = {'state': 'initial'}
            elif not conv['context'].get('state'):
                conv['context']['state'] = 'initial'
            
            conversation = Conversation(**conv)
            print(f"Conversación encontrada: {conversation.model_dump_json(indent=2)}")
            return conversation
            
        except Exception as e:
            print(f"Error en get_conversation: {str(e)}")
            raise e
    
    async def get_active_conversation(self, user_id: str) -> Optional[Conversation]:
        """Get active conversation for a user"""
        try:
            print(f"\n=== BUSCANDO CONVERSACIÓN ACTIVA ===")
            print(f"Usuario ID: {user_id}")
            
            # Buscar conversación activa
            conversations = await self.db.query_collection(
                'conversations',
                'user_id',
                '==',
                user_id,
                additional_filters=[('active', '==', True)]
            )
            
            if not conversations:
                print("No se encontró conversación activa")
                return None
            
            # Convertir a modelo
            conv_data = conversations[0]
            
            # Convertir timestamps
            if isinstance(conv_data.get('created_at'), str):
                conv_data['created_at'] = datetime.fromisoformat(conv_data['created_at'])
            if isinstance(conv_data.get('updated_at'), str):
                conv_data['updated_at'] = datetime.fromisoformat(conv_data['updated_at'])
            
            # Convertir mensajes
            messages = []
            for msg in conv_data.get('messages', []):
                if isinstance(msg.get('timestamp'), str):
                    msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
                messages.append(Message(**msg))
            conv_data['messages'] = messages
            
            # Asegurar que el contexto tenga un estado válido
            if not conv_data.get('context'):
                conv_data['context'] = {'state': 'initial'}
            elif not conv_data['context'].get('state'):
                conv_data['context']['state'] = 'initial'
            
            conversation = Conversation(**conv_data)
            print(f"Conversación activa encontrada: {conversation.model_dump_json(indent=2)}")
            return conversation
            
        except Exception as e:
            print(f"Error en get_active_conversation: {str(e)}")
            raise e
    
    async def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Add a message to a conversation"""
        try:
            print(f"\n=== AGREGANDO MENSAJE A CONVERSACIÓN ===")
            print(f"ID: {conversation_id}")
            print(f"Role: {role}")
            print(f"Content: {content}")
            
            # 1. Obtener conversación
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # 2. Validar role
            if role not in ['user', 'bot']:
                raise ValueError(f"Invalid role: {role}")
            
            # 3. Crear mensaje con timestamp actual
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.now()
            )
            
            # 4. Agregar mensaje y actualizar timestamps
            conversation.messages.append(message)
            conversation.updated_at = datetime.now()
            
            # 5. Guardar en base de datos
            conv_dict = conversation.model_dump()
            await self.db.update_document('conversations', conversation_id, conv_dict)
            
            print(f"Mensaje agregado: {message.model_dump_json(indent=2)}")
            return True
            
        except Exception as e:
            print(f"Error en add_message: {str(e)}")
            raise e
    
    async def update_conversation_context(self, conversation_id: str, new_context: Dict) -> bool:
        """Update conversation context"""
        try:
            print(f"\n=== ACTUALIZANDO CONTEXTO DE CONVERSACIÓN ===")
            print(f"ID: {conversation_id}")
            print(f"Nuevo contexto: {json.dumps(new_context, indent=2)}")
            
            # 1. Obtener conversación actual
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # 2. Validar el estado
            if 'state' in new_context and not new_context['state']:
                raise ValueError("State cannot be empty")
            
            # 3. Merge context instead of overwrite
            current_context = conversation.context or {}
            merged_context = {**current_context, **new_context}
            
            # 4. Actualizar timestamps
            conversation.context = merged_context
            conversation.updated_at = datetime.now()
            
            # 5. Guardar en base de datos
            conv_dict = conversation.model_dump()
            await self.db.update_document('conversations', conversation_id, conv_dict)
            
            print(f"Contexto actualizado: {json.dumps(merged_context, indent=2)}")
            return True
            
        except Exception as e:
            print(f"Error en update_conversation_context: {str(e)}")
            raise e
    
    async def reset_conversation(self, conversation_id: str) -> bool:
        """Reset a conversation to initial state"""
        try:
            print(f"\n=== RESETEANDO CONVERSACIÓN ===")
            print(f"ID: {conversation_id}")
            
            # 1. Obtener conversación actual
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # 2. Preservar datos importantes del contexto
            current_context = conversation.context or {}
            preserved_data = {
                'user_name': current_context.get('user_name'),
                'phone_number': current_context.get('phone_number')
            }
            
            # 3. Resetear contexto pero preservar datos importantes
            conversation.context = {
                'state': 'initial',
                **{k: v for k, v in preserved_data.items() if v is not None}
            }
            
            # 4. Actualizar timestamps
            conversation.updated_at = datetime.now()
            
            # 5. Guardar en base de datos
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
