"""
Módulo para manejar la interacción con Firebase
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
from app.utils.constants import ConversationState

logger = logging.getLogger(__name__)

class FirebaseDB:
    """Maneja la interacción con Firebase y el caché local"""
    
    def __init__(self):
        """Inicializa el cliente de Firestore y el caché"""
        try:
            # Inicializar Firebase Admin
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            # Caché con tiempo de vida de 5 minutos
            self.cache = TTLCache(maxsize=100, ttl=300)
            
        except Exception as e:
            logger.error(f"Error inicializando Firebase: {str(e)}")
            raise
    
    async def get_conversation_state(self, phone: str) -> Optional[ConversationState]:
        """
        Obtiene el estado actual de la conversación
        
        Args:
            phone: Número de teléfono del usuario
            
        Returns:
            Optional[ConversationState]: Estado actual de la conversación
        """
        try:
            # Intentar obtener del caché
            cache_key = f"state_{phone}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Si no está en caché, obtener de Firebase
            user_ref = self.db.collection('users').document(phone)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                state = user_doc.to_dict().get('state')
                if state:
                    self.cache[cache_key] = state
                    return state
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de conversación: {str(e)}")
            return None
    
    async def update_user_state(self, phone: str, state: ConversationState) -> bool:
        """
        Actualiza el estado de la conversación del usuario
        
        Args:
            phone: Número de teléfono del usuario
            state: Nuevo estado de la conversación
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Actualizar en Firebase
            user_ref = self.db.collection('users').document(phone)
            user_ref.set({
                'state': state,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            # Actualizar caché
            cache_key = f"state_{phone}"
            self.cache[cache_key] = state
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estado de usuario: {str(e)}")
            return False
    
    async def get_user_data(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos del usuario
        
        Args:
            phone: Número de teléfono del usuario
            
        Returns:
            Optional[Dict[str, Any]]: Datos del usuario
        """
        try:
            # Intentar obtener del caché
            cache_key = f"data_{phone}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Si no está en caché, obtener de Firebase
            user_ref = self.db.collection('users').document(phone)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                data = user_doc.to_dict().get('data', {})
                self.cache[cache_key] = data
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de usuario: {str(e)}")
            return None
    
    async def update_user_data(self, phone: str, data: Dict[str, Any]) -> bool:
        """
        Actualiza los datos del usuario
        
        Args:
            phone: Número de teléfono del usuario
            data: Nuevos datos a guardar
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Obtener datos actuales
            current_data = await self.get_user_data(phone) or {}
            
            # Actualizar datos
            current_data.update(data)
            
            # Guardar en Firebase
            user_ref = self.db.collection('users').document(phone)
            user_ref.set({
                'data': current_data,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            # Actualizar caché
            cache_key = f"data_{phone}"
            self.cache[cache_key] = current_data
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando datos de usuario: {str(e)}")
            return False
    
    async def update_user_name(self, phone: str, name: str) -> bool:
        """
        Actualiza el nombre del usuario
        
        Args:
            phone: Número de teléfono del usuario
            name: Nombre del usuario
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            user_ref = self.db.collection('users').document(phone)
            user_ref.set({
                'name': name,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando nombre de usuario: {str(e)}")
            return False
    
    async def reset_user_state(self, phone: str) -> bool:
        """
        Reinicia el estado de la conversación del usuario
        
        Args:
            phone: Número de teléfono del usuario
            
        Returns:
            bool: True si se reinició correctamente
        """
        try:
            # Limpiar caché
            cache_key_state = f"state_{phone}"
            cache_key_data = f"data_{phone}"
            self.cache.pop(cache_key_state, None)
            self.cache.pop(cache_key_data, None)
            
            # Actualizar en Firebase
            user_ref = self.db.collection('users').document(phone)
            user_ref.set({
                'state': ConversationState.INITIAL,
                'data': {},
                'reset_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error reiniciando estado de usuario: {str(e)}")
            return False

# Instancia global
firebase_manager = FirebaseDB()
