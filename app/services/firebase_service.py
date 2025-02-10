import os
from typing import Dict, List, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

class FirebaseService:
    def __init__(self):
        cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def save_user_data(self, phone_number: str, data: Dict) -> str:
        """
        Guarda o actualiza datos del usuario
        """
        doc_ref = self.db.collection('users').document(phone_number)
        doc_ref.set(data, merge=True)
        return phone_number

    def save_conversation(self, phone_number: str, message_data: Dict) -> str:
        """
        Guarda un mensaje de la conversación
        """
        conversation_ref = self.db.collection('conversations').document(phone_number)
        conversation_ref.collection('messages').add({
            **message_data,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return phone_number

    def get_user_data(self, phone_number: str) -> Optional[Dict]:
        """
        Obtiene datos del usuario
        """
        doc_ref = self.db.collection('users').document(phone_number)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None

    def get_conversation_history(self, phone_number: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene historial de conversación
        """
        messages_ref = (self.db.collection('conversations')
                       .document(phone_number)
                       .collection('messages')
                       .order_by('timestamp', direction=firestore.Query.DESCENDING)
                       .limit(limit))
        
        return [doc.to_dict() for doc in messages_ref.stream()]

    def save_score(self, phone_number: str, score_data: Dict) -> str:
        """
        Guarda el Fingro Score calculado
        """
        score_ref = self.db.collection('scores').document(phone_number)
        score_ref.set({
            **score_data,
            'timestamp': firestore.SERVER_TIMESTAMP
        }, merge=True)
        return phone_number

    def get_latest_score(self, phone_number: str) -> Optional[Dict]:
        """
        Obtiene el último Fingro Score calculado
        """
        score_ref = self.db.collection('scores').document(phone_number)
        doc = score_ref.get()
        return doc.to_dict() if doc.exists else None
