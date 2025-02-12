"""
Módulo para manejar la interacción con Firebase
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache
import firebase_admin
from firebase_admin import credentials, firestore, App
from app.config import settings
from app.utils.constants import ConversationState

logger = logging.getLogger(__name__)

class FirebaseDB:
    """Maneja la interacción con Firebase y el caché local"""
    
    def __init__(self):
        """Inicializa el cliente de Firestore y el caché"""
        try:
            # Intentar obtener app existente o crear nueva
            try:
                self.app = firebase_admin.get_app()
            except ValueError:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
                self.app = firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            # Caché con tiempo de vida configurable
            self.cache = TTLCache(
                maxsize=settings.FIREBASE_CACHE_MAXSIZE,
                ttl=settings.FIREBASE_CACHE_TTL
            )
            
        except Exception as e:
            logger.error(f"Error inicializando Firebase: {str(e)}")
            raise
    
    async def get_conversation_state(self, phone: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la conversación
        
        Args:
            phone: Número de teléfono del usuario
            
        Returns:
            Dict[str, Any]: Estado actual de la conversación y datos del usuario
        """
        try:
            # Intentar obtener del caché de forma segura
            cache_key = f"state_{phone}"
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Si no está en caché, obtener de Firebase
            user_ref = self.db.collection('users').document(phone)
            doc = user_ref.get()  # No es necesario await aquí
            
            if doc.exists:
                data = doc.to_dict()
            else:
                # Si no existe, crear estado inicial
                data = {
                    'state': ConversationState.INITIAL.value,
                    'data': {},
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                user_ref.set(data)  # No es necesario await aquí
            
            # Guardar en caché
            self.cache[cache_key] = data
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de conversación: {str(e)}")
            # Retornar estado inicial en caso de error
            return {
                'state': ConversationState.INITIAL.value,
                'data': {}
            }
    
    async def update_user_state(self, phone: str, state: Dict[str, Any]) -> bool:
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
            state['updated_at'] = firestore.SERVER_TIMESTAMP
            user_ref.set(state, merge=True)  # No es necesario await aquí
            
            # Actualizar caché de forma segura
            cache_key = f"state_{phone}"
            self.cache[cache_key] = state
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estado: {str(e)}")
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
            # Crear estado inicial
            initial_state = {
                'state': ConversationState.INITIAL.value,
                'data': {},
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Actualizar en Firebase
            user_ref = self.db.collection('users').document(phone)
            await user_ref.set(initial_state, merge=True)
            
            # Limpiar caché
            cache_key = f"state_{phone}"
            self.cache.pop(cache_key, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Error reiniciando estado: {str(e)}")
            return False
    
    async def store_analysis(self, phone: str, analysis: Dict[str, Any]) -> bool:
        """
        Guarda el análisis generado para un usuario
        
        Args:
            phone: Número de teléfono del usuario
            analysis: Datos del análisis
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Sanitizar datos sensibles
            safe_analysis = self._sanitize_data(analysis)
            
            # Crear documento de análisis
            analysis_data = {
                'user_phone': phone,
                'analysis': safe_analysis,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # Guardar en Firebase
            await self.db.collection('analysis').add(analysis_data)
            return True
            
        except Exception as e:
            logger.error(f"Error guardando análisis: {str(e)}")
            return False
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza datos sensibles antes de guardar o loggear
        
        Args:
            data: Datos a sanitizar
            
        Returns:
            Dict[str, Any]: Datos sanitizados
        """
        sensitive_fields = ['phone', 'email', 'address']
        safe_data = data.copy()
        
        for field in sensitive_fields:
            if field in safe_data:
                safe_data[field] = '[REDACTED]'
        
        return safe_data

# Instancia global
firebase_manager = FirebaseDB()
