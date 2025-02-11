from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime
import os
import json
from typing import Any, Optional

class FirestoreDB:
    def __init__(self):
        """Inicializa la conexión con Firestore"""
        try:
            # Intentar obtener credenciales desde variable de entorno
            cred_json = os.getenv('FIREBASE_CREDENTIALS')
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                # Fallback a archivo local
                cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
                cred = credentials.Certificate(cred_path)
            
            initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Error inicializando Firebase: {str(e)}")
            raise

    async def get_user(self, phone_number: str) -> Optional[dict[str, Any]]:
        """Obtiene los datos de un usuario por su número de teléfono"""
        doc_ref = self.db.collection('users').document(phone_number)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
        
    async def create_or_update_user(self, phone_number: str, data: dict[str, Any]) -> None:
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
            
    async def update_conversation_state(self, phone_number: str, state: str, conversation_data: dict[str, Any]) -> None:
        """Actualiza el estado de la conversación y los datos recopilados"""
        doc_ref = self.db.collection('users').document(phone_number)
        current_time = datetime.now().isoformat()
        
        doc_ref.update({
            'estado_conversacion': state,
            'data': conversation_data,
            'updated_at': current_time
        })
        
    async def create_solicitud(self, phone_number: str, data: dict[str, Any]) -> str:
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

    async def delete_user_data(self, phone_number: str):
        """Borra todos los datos asociados a un usuario"""
        try:
            # Borrar documento del usuario
            user_ref = self.db.collection('users').document(phone_number)
            user_ref.delete()
            
            # Borrar solicitudes asociadas
            solicitudes = self.db.collection('solicitudes').where('user_id', '==', phone_number).stream()
            for solicitud in solicitudes:
                solicitud.reference.delete()
            
            return True
        except Exception as e:
            print(f"Error borrando datos del usuario: {str(e)}")
            return False

# Instancia global de la base de datos
db = FirestoreDB()
