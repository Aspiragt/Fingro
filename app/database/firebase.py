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
        
    def _get_user_ref(self, phone: str) -> firestore.DocumentReference:
        """Obtiene la referencia al documento del usuario"""
        return self.db.collection('users').document(phone)
        
    def get_user_state(self, phone: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual del usuario desde el caché o Firebase
        """
        try:
            # Intentar obtener del caché
            cache_key = f"state_{phone}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Si no está en caché, obtener de Firebase
            user_ref = self._get_user_ref(phone)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                # Usuario nuevo
                state = {
                    'state': ConversationState.INICIO,
                    'data': {},
                    'last_activity': datetime.now().isoformat(),
                    'name': None
                }
                user_ref.set(state)
            else:
                state = user_doc.to_dict()
                # Actualizar última actividad
                user_ref.update({'last_activity': datetime.now().isoformat()})
            
            # Guardar en caché
            self.cache[cache_key] = state
            return state
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del usuario {phone}: {str(e)}")
            return {
                'state': ConversationState.INICIO,
                'data': {},
                'last_activity': datetime.now().isoformat(),
                'name': None
            }
    
    def update_user_state(self, phone: str, new_state: str, data: Dict[str, Any] = None) -> None:
        """
        Actualiza el estado del usuario en Firebase y caché
        """
        try:
            user_ref = self._get_user_ref(phone)
            update_data = {
                'state': new_state,
                'last_activity': datetime.now().isoformat()
            }
            
            if data:
                update_data['data'] = data
            
            # Actualizar en Firebase
            user_ref.update(update_data)
            
            # Actualizar caché
            cache_key = f"state_{phone}"
            if cache_key in self.cache:
                cached_state = self.cache[cache_key]
                cached_state.update(update_data)
                self.cache[cache_key] = cached_state
                
        except Exception as e:
            logger.error(f"Error actualizando estado del usuario {phone}: {str(e)}")
    
    def update_user_name(self, phone: str, name: str) -> None:
        """
        Actualiza el nombre del usuario
        """
        try:
            user_ref = self._get_user_ref(phone)
            user_ref.update({'name': name})
            
            # Actualizar caché
            cache_key = f"state_{phone}"
            if cache_key in self.cache:
                cached_state = self.cache[cache_key]
                cached_state['name'] = name
                self.cache[cache_key] = cached_state
                
        except Exception as e:
            logger.error(f"Error actualizando nombre del usuario {phone}: {str(e)}")
    
    def reset_conversation(self, phone: str) -> None:
        """
        Reinicia la conversación del usuario
        """
        try:
            # Limpiar datos en Firebase
            user_ref = self._get_user_ref(phone)
            user_ref.set({
                'state': ConversationState.INICIO,
                'data': {},
                'last_activity': datetime.now().isoformat(),
                'name': None
            })
            
            # Limpiar caché
            cache_key = f"state_{phone}"
            if cache_key in self.cache:
                del self.cache[cache_key]
                
        except Exception as e:
            logger.error(f"Error reiniciando conversación del usuario {phone}: {str(e)}")
    
    def save_fingro_score(self, phone: str, score_data: Dict[str, Any]) -> None:
        """
        Guarda el Fingro Score y datos financieros del usuario
        """
        try:
            user_ref = self._get_user_ref(phone)
            score_doc = {
                'score_data': score_data,
                'calculated_at': datetime.now().isoformat()
            }
            user_ref.collection('scores').add(score_doc)
            
            # Actualizar datos del usuario
            user_ref.update({
                'latest_score': score_data,
                'score_updated_at': datetime.now().isoformat()
            })
            
            # Actualizar caché
            cache_key = f"state_{phone}"
            if cache_key in self.cache:
                cached_state = self.cache[cache_key]
                cached_state['latest_score'] = score_data
                cached_state['score_updated_at'] = datetime.now().isoformat()
                self.cache[cache_key] = cached_state
                
        except Exception as e:
            logger.error(f"Error guardando Fingro Score para usuario {phone}: {str(e)}")

# Instancia global
firebase_manager = FirebaseDB()
