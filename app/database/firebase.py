"""
Módulo para interactuar con Firebase
"""
import json
import logging
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore

from app.config import settings

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
                
                # Inicializar app
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase app initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Firebase: {str(e)}")
                raise
        
        # Inicializar Firestore
        self.db = firestore.client()
        
    async def get_conversation_state(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de la conversación para un usuario
        
        Args:
            phone: Número de teléfono del usuario
            
        Returns:
            Dict con el estado o None si no existe
        """
        try:
            doc_ref = self.db.collection('users').document(phone)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting conversation state: {str(e)}")
            return None
    
    async def update_user_state(self, phone: str, state: Dict[str, Any]) -> bool:
        """
        Actualiza el estado de un usuario
        
        Args:
            phone: Número de teléfono del usuario
            state: Nuevo estado
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            doc_ref = self.db.collection('users').document(phone)
            doc_ref.set(state, merge=True)
            return True
        except Exception as e:
            logger.error(f"Error updating user state: {str(e)}")
            return False

    async def update_conversation_state(self, phone: str, new_state: str) -> bool:
        """
        Actualiza el estado de la conversación
        
        Args:
            phone: Número de teléfono del usuario
            new_state: Nuevo estado de la conversación
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            current_state = await self.get_conversation_state(phone)
            if current_state is None:
                current_state = {}
            current_state['state'] = new_state
            return await self.update_user_state(phone, current_state)
        except Exception as e:
            logger.error(f"Error actualizando estado de conversación: {str(e)}")
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
                'state': 'INITIAL',
                'data': {}
            }
            
            # Actualizar en Firebase
            user_ref = self.db.collection('users').document(phone)
            result = user_ref.set(initial_state, merge=True)
            
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
            result = self.db.collection('analysis').add(analysis_data)
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
