"""
Módulo para interactuar con Firebase
"""
import json
import logging
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import AsyncClient
from datetime import datetime, timedelta

from app.config import settings
from app.utils.text import sanitize_data

logger = logging.getLogger(__name__)

class FirebaseDB:
    """Clase para manejar la conexión con Firebase"""
    
    def __init__(self):
        """Inicializa la conexión con Firebase"""
        try:
            # Intentar obtener la app existente
            self.app = firebase_admin.get_app()
            logger.info("Using existing Firebase app")
        except ValueError:
            # Si no existe, inicializar con las credenciales
            try:
                if not settings.FIREBASE_CREDENTIALS:
                    raise ValueError("Firebase credentials not found in environment")
                
                # Convertir el string JSON a diccionario
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS)
                cred = credentials.Certificate(cred_dict)
                
                # Inicializar app con configuración de retry
                self.app = firebase_admin.initialize_app(cred, {
                    'httpTimeout': 30,
                    'retryTimeoutSeconds': 600,
                    'maxRetries': 3
                })
                logger.info("Firebase app initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Firebase: {str(e)}")
                raise
        
        # Inicializar Firestore de manera asíncrona
        self.db = AsyncClient(self.app)
        
        # Cache para estados de conversación
        self._conversation_cache = {}
        self._cache_timeout = timedelta(minutes=5)
        
    async def get_conversation_state(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de la conversación para un usuario
        
        Args:
            phone: Número de teléfono del usuario (debe estar validado)
            
        Returns:
            Dict con el estado o None si no existe
        """
        try:
            # Verificar cache
            cache_key = f"conv_state_{phone}"
            cached = self._conversation_cache.get(cache_key)
            if cached and cached['timestamp'] + self._cache_timeout > datetime.now():
                return cached['data']

            # Obtener de Firestore
            doc_ref = self.db.collection('users').document(phone)
            doc = await doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Validar estructura del estado
                if not self._validate_state_structure(data):
                    logger.warning(f"Invalid state structure for {phone}")
                    data = self._create_default_state()
                
                # Actualizar cache
                self._conversation_cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now()
                }
                return data
                
            return self._create_default_state()
            
        except Exception as e:
            logger.error(f"Error getting conversation state: {str(e)}")
            raise FirebaseError("Error retrieving conversation state") from e
    
    async def update_user_state(self, phone: str, state: Dict[str, Any], merge: bool = True) -> bool:
        """
        Actualiza el estado de un usuario
        
        Args:
            phone: Número de teléfono del usuario
            state: Nuevo estado
            merge: Si se debe hacer merge con el estado existente
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Sanitizar datos antes de guardar
            safe_state = sanitize_data(state)
            
            # Validar estructura
            if not self._validate_state_structure(safe_state):
                raise ValueError("Invalid state structure")
            
            # Actualizar en Firestore
            doc_ref = self.db.collection('users').document(phone)
            await doc_ref.set(safe_state, merge=merge)
            
            # Actualizar cache
            cache_key = f"conv_state_{phone}"
            if merge and cache_key in self._conversation_cache:
                self._conversation_cache[cache_key]['data'].update(safe_state)
            else:
                self._conversation_cache[cache_key] = {
                    'data': safe_state,
                    'timestamp': datetime.now()
                }
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating user state: {str(e)}")
            raise FirebaseError("Error updating user state") from e

    def _validate_state_structure(self, state: Dict[str, Any]) -> bool:
        """Valida la estructura del estado"""
        required_fields = {'state', 'last_interaction', 'data'}
        return all(field in state for field in required_fields)
        
    def _create_default_state(self) -> Dict[str, Any]:
        """Crea un estado por defecto"""
        return {
            'state': 'INICIO',
            'last_interaction': datetime.now().isoformat(),
            'data': {},
            'session_id': None
        }

class FirebaseError(Exception):
    """Excepción personalizada para errores de Firebase"""
    pass

# Instancia global
firebase_manager = FirebaseDB()
