from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime
import os
from typing import Dict, Any, Optional

class FirestoreDB:
    def __init__(self):
        """Inicializa la conexión con Firestore"""
        cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json'))
        initialize_app(cred)
        self.db = firestore.client()
        
    async def get_user(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un usuario por su número de teléfono"""
        doc_ref = self.db.collection('users').document(phone_number)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
        
    async def create_or_update_user(self, phone_number: str, data: Dict[str, Any]) -> None:
        """Crea o actualiza los datos de un usuario"""
        doc_ref = self.db.collection('users').document(phone_number)
        current_time = datetime.now().isoformat()
        
        if doc_ref.get().exists:
            # Actualizar usuario existente
            doc_ref.update({
                **data,
                'updated_at': current_time
            })
        else:
            # Crear nuevo usuario
            doc_ref.set({
                **data,
                'created_at': current_time,
                'updated_at': current_time
            })
            
    async def update_conversation_state(self, phone_number: str, state: str, conversation_data: Dict[str, Any]) -> None:
        """Actualiza el estado de la conversación y los datos recopilados"""
        doc_ref = self.db.collection('users').document(phone_number)
        current_time = datetime.now().isoformat()
        
        doc_ref.update({
            'estado_conversacion': state,
            'data': conversation_data,
            'updated_at': current_time
        })
        
    async def create_solicitud(self, phone_number: str, data: Dict[str, Any]) -> str:
        """Crea una nueva solicitud de financiamiento"""
        solicitud_ref = self.db.collection('solicitudes').document()
        current_time = datetime.now().isoformat()
        
        solicitud_data = {
            'user_id': phone_number,
            'estado': 'NUEVA',
            'fecha_solicitud': current_time,
            **data
        }
        
        solicitud_ref.set(solicitud_data)
        return solicitud_ref.id

# Instancia global de la base de datos
db = FirestoreDB()
