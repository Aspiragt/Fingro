"""Módulo para manejar la conexión con Firestore"""
from typing import Optional, Dict, Any
from google.cloud import firestore
from app.chat.conversation_flow import ConversationState, ProjectData

class FirestoreDB:
    def __init__(self, db: firestore.Client):
        self.firebase_db = db
        self.conversations_ref = self.firebase_db.collection('conversations')
    
    def get_conversation_state(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de la conversación para un número de teléfono"""
        doc_ref = self.conversations_ref.document(phone_number)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def save_conversation_state(self, phone_number: str, state: ConversationState, project_data: ProjectData) -> None:
        """Guarda el estado de la conversación"""
        doc_ref = self.conversations_ref.document(phone_number)
        doc_ref.set({
            'state': state.value,
            'project_data': {
                'crop_name': project_data.crop_name,
                'area_ha': project_data.area_ha,
                'market_type': project_data.market_type.value if project_data.market_type else None,
                'irrigation_type': project_data.irrigation_type.value if project_data.irrigation_type else None,
                'location': project_data.location,
                'created_at': project_data.created_at
            }
        })
    
    def reset_conversation(self, phone_number: str) -> None:
        """Reinicia la conversación borrando el estado actual"""
        doc_ref = self.conversations_ref.document(phone_number)
        doc_ref.delete()
    
    def reset_all_conversations(self) -> None:
        """Reinicia todas las conversaciones"""
        batch = self.firebase_db.batch()
        docs = self.conversations_ref.stream()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()
