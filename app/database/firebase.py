import os
from typing import Optional, Dict, Any, List
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from functools import lru_cache
import logging
from cachetools import TTLCache, cached

logger = logging.getLogger(__name__)

class FirebaseDB:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
            # Caché para estados de conversación (TTL de 1 hora)
            self._conversation_cache = TTLCache(maxsize=1000, ttl=3600)
            # Caché para datos de usuario (TTL de 24 horas)
            self._user_cache = TTLCache(maxsize=1000, ttl=86400)

    @lru_cache(maxsize=1)
    def _get_credentials(self) -> Dict[str, str]:
        """Get Firebase credentials from environment variables"""
        required_vars = [
            'FIREBASE_PROJECT_ID',
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        return {
            'type': 'service_account',
            'project_id': os.getenv('FIREBASE_PROJECT_ID'),
            'private_key': os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
            'client_email': os.getenv('FIREBASE_CLIENT_EMAIL'),
            'token_uri': 'https://oauth2.googleapis.com/token'
        }

    def _initialize_firebase(self) -> None:
        """Initialize Firebase connection"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self._get_credentials())
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            raise

    def get_user(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user data with caching"""
        # Intentar obtener del caché primero
        if phone_number in self._user_cache:
            logger.debug(f"Cache hit for user {phone_number}")
            return self._user_cache[phone_number]

        # Si no está en caché, obtener de Firebase
        doc = self.db.collection('users').document(phone_number).get()
        if doc.exists:
            user_data = doc.to_dict()
            self._user_cache[phone_number] = user_data
            return user_data
        return None

    def create_user(self, phone_number: str, data: Dict[str, Any]) -> None:
        """Create new user"""
        self.db.collection('users').document(phone_number).set(data)
        # Actualizar caché
        self._user_cache[phone_number] = data

    def update_user(self, phone_number: str, data: Dict[str, Any]) -> None:
        """Update user data"""
        self.db.collection('users').document(phone_number).set(data, merge=True)
        # Actualizar caché
        if phone_number in self._user_cache:
            self._user_cache[phone_number].update(data)

    def get_conversation_state(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get conversation state with caching"""
        # Intentar obtener del caché primero
        if phone_number in self._conversation_cache:
            logger.debug(f"Cache hit for conversation state {phone_number}")
            return self._conversation_cache[phone_number]

        # Si no está en caché, obtener del usuario
        user = self.get_user(phone_number)
        if user:
            state = user.get('conversation_state')
            if state:
                self._conversation_cache[phone_number] = state
            return state
        return None

    def update_conversation_state(self, phone_number: str, conversation_data: Dict[str, Any]) -> None:
        """Update conversation state with caching"""
        try:
            user_ref = self.db.collection('users').document(phone_number)
            doc = user_ref.get()
            
            if doc.exists:
                # Actualizar estado existente
                user_ref.update({'conversation_state': conversation_data})
            else:
                # Crear nuevo usuario con estado inicial
                user_ref.set({
                    'phone_number': phone_number,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'conversation_state': conversation_data
                })
            
            # Actualizar caché
            self._conversation_cache[phone_number] = conversation_data
            
        except Exception as e:
            logger.error(f"Error updating conversation state: {str(e)}")
            raise

    def reset_conversation(self, phone_number: str) -> None:
        """Reset conversation state"""
        try:
            initial_state = {
                'state': 'INICIO',
                'data': {}
            }
            self.update_conversation_state(phone_number, initial_state)
            # Limpiar caché
            if phone_number in self._conversation_cache:
                del self._conversation_cache[phone_number]
        except Exception as e:
            logger.error(f"Error resetting conversation: {str(e)}")
            raise

    def add_message(self, phone_number: str, message: Dict[str, Any]) -> None:
        """Add message to conversation history"""
        message['timestamp'] = firestore.SERVER_TIMESTAMP
        self.db.collection('conversations').document(phone_number).collection('messages').add(message)

    def get_messages(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history"""
        messages = (self.db.collection('conversations')
                   .document(phone_number)
                   .collection('messages')
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .stream())
        return [msg.to_dict() for msg in messages]

    def collection(self, name: str):
        """Get a collection reference"""
        return self.db.collection(name)
    
    async def add_document(self, collection: str, data: dict, doc_id: str = None):
        """Add a document to a collection"""
        try:
            if doc_id:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.set(data)
                return doc_id
            else:
                doc_ref = self.db.collection(collection).add(data)
                return doc_ref[1].id
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise e
    
    async def get_document(self, collection: str, doc_id: str):
        """Get a document by ID"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise e
    
    async def update_document(self, collection: str, doc_id: str, data: dict):
        """Update a document"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise e
    
    async def delete_document(self, collection: str, doc_id: str):
        """Delete a document"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise e
    
    async def query_collection(self, collection: str, field: str, operator: str, value: any):
        """Query documents in a collection"""
        try:
            docs = self.db.collection(collection).where(field, operator, value).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error querying collection: {str(e)}")
            raise e

# Singleton instance
db = FirebaseDB()
