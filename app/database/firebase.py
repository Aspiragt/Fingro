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

class FirebaseError(Exception):
    """Excepción personalizada para errores de Firebase"""
    pass

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
                if 'project_id' not in cred_dict:
                    raise ValueError("project_id not found in Firebase credentials")
                
                cred = credentials.Certificate(cred_dict)
                self.app = firebase_admin.initialize_app(cred)
                logger.info(f"Firebase app initialized successfully for project: {cred_dict['project_id']}")
            except json.JSONDecodeError:
                logger.error("Invalid JSON in FIREBASE_CREDENTIALS")
                raise FirebaseError("Invalid Firebase credentials format")
            except Exception as e:
                logger.error(f"Error initializing Firebase: {str(e)}")
                raise
        
        try:
            # Inicializar Firestore de manera asíncrona
            self.db = AsyncClient(self.app)
            logger.info("Firestore client initialized successfully")
            
            # Cache para estados de conversación
            self._conversation_cache = {}
            self._cache_timeout = timedelta(minutes=5)
            
        except Exception as e:
            logger.error(f"Error initializing Firestore client: {str(e)}")
            raise FirebaseError(f"Failed to initialize Firestore: {str(e)}")
        
    async def get_conversation_state(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de la conversación para un usuario
        
        Args:
            phone: Número de teléfono del usuario (debe estar validado)
            
        Returns:
            Optional[Dict[str, Any]]: Estado de la conversación o None si no existe
        """
        try:
            # Verificar caché primero
            if phone in self._conversation_cache:
                cached_state, timestamp = self._conversation_cache[phone]
                if datetime.now() - timestamp < self._cache_timeout:
                    return cached_state
            
            # Si no está en caché o expiró, obtener de Firestore
            doc_ref = self.db.collection('conversations').document(phone)
            doc = await doc_ref.get()
            
            if doc.exists:
                state = doc.to_dict()
                # Actualizar caché
                self._conversation_cache[phone] = (state, datetime.now())
                return state
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation state: {str(e)}")
            raise FirebaseError(f"Failed to get conversation state: {str(e)}")
    
    async def update_user_state(self, phone: str, state: Dict[str, Any]):
        """
        Actualiza el estado de un usuario
        
        Args:
            phone: Número de teléfono del usuario
            state: Nuevo estado
        """
        try:
            # Sanitizar datos antes de guardar
            clean_state = sanitize_data(state)
            
            # Guardar en Firestore
            doc_ref = self.db.collection('conversations').document(phone)
            await doc_ref.set(clean_state, merge=True)
            
            # Actualizar caché
            self._conversation_cache[phone] = (clean_state, datetime.now())
            
        except Exception as e:
            logger.error(f"Error updating user state: {str(e)}")
            raise FirebaseError(f"Failed to update user state: {str(e)}")

# Instancia global
firebase_manager = FirebaseDB()
