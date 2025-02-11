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
            
            if user_doc.exists:
                state = user_doc.to_dict()
            else:
                state = {
                    'state': ConversationState.INITIAL.value,
                    'data': {},
                    'last_update': datetime.utcnow().isoformat()
                }
                user_ref.set(state)
            
            # Guardar en caché
            self.cache[cache_key] = state
            return state
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del usuario {phone}: {str(e)}")
            return {
                'state': ConversationState.INITIAL.value,
                'data': {},
                'last_update': datetime.utcnow().isoformat()
            }
    
    def get_conversation_state(self, phone: str) -> Dict[str, Any]:
        """
        Obtiene el estado de la conversación del usuario
        """
        return self.get_user_state(phone)
    
    def update_user_state(self, phone: str, state: Dict[str, Any]) -> None:
        """
        Actualiza el estado del usuario en Firebase y caché
        """
        try:
            # Actualizar timestamp
            state['last_update'] = datetime.utcnow().isoformat()
            
            # Actualizar en Firebase
            user_ref = self._get_user_ref(phone)
            user_ref.set(state, merge=True)
            
            # Actualizar caché
            cache_key = f"state_{phone}"
            self.cache[cache_key] = state
            
        except Exception as e:
            logger.error(f"Error actualizando estado del usuario {phone}: {str(e)}")
            raise
    
    def reset_user_state(self, phone: str) -> None:
        """
        Reinicia el estado del usuario a inicial
        """
        try:
            initial_state = {
                'state': ConversationState.INITIAL.value,
                'data': {},
                'last_update': datetime.utcnow().isoformat()
            }
            self.update_user_state(phone, initial_state)
            
        except Exception as e:
            logger.error(f"Error reiniciando estado del usuario {phone}: {str(e)}")
            raise
    
    def store_analysis(self, phone: str, analysis_data: Dict[str, Any]) -> None:
        """
        Almacena los resultados del análisis financiero
        """
        try:
            analysis_ref = self.db.collection('analysis').document()
            analysis_data.update({
                'user_phone': phone,
                'created_at': datetime.utcnow().isoformat()
            })
            analysis_ref.set(analysis_data)
            
        except Exception as e:
            logger.error(f"Error almacenando análisis para usuario {phone}: {str(e)}")
            raise
    
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
                'state': ConversationState.INITIAL.value,
                'data': {},
                'last_update': datetime.utcnow().isoformat(),
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
                'calculated_at': datetime.utcnow().isoformat()
            }
            user_ref.collection('scores').add(score_doc)
            
            # Actualizar datos del usuario
            user_ref.update({
                'latest_score': score_data,
                'score_updated_at': datetime.utcnow().isoformat()
            })
            
            # Actualizar caché
            cache_key = f"state_{phone}"
            if cache_key in self.cache:
                cached_state = self.cache[cache_key]
                cached_state['latest_score'] = score_data
                cached_state['score_updated_at'] = datetime.utcnow().isoformat()
                self.cache[cache_key] = cached_state
                
        except Exception as e:
            logger.error(f"Error guardando Fingro Score para usuario {phone}: {str(e)}")

# Instancia global
firebase_manager = FirebaseDB()
