import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
import os
import json
from dotenv import load_dotenv

load_dotenv()

class FirebaseDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseDB, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Firebase connection"""
        try:
            # Crear el diccionario de credenciales desde variables de entorno
            cred_dict = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.getenv("FIREBASE_PRIVATE_KEY") else None,
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
            }
            
            # Verificar que todas las credenciales necesarias están presentes
            required_fields = ["project_id", "private_key", "client_email"]
            missing_fields = [field for field in required_fields if not cred_dict.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required Firebase credentials: {', '.join(missing_fields)}")
            
            # Inicializar Firebase
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            print("Firebase initialized successfully")
            
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            raise e
    
    def collection(self, name: str):
        """Get a collection reference"""
        return self.db.collection(name)
    
    async def add_document(self, collection: str, data: dict, doc_id: str = None):
        """Add a document to a collection"""
        try:
            if doc_id:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.set(data)
                return doc_id
            else:
                doc_ref = self.db.collection(collection).add(data)
                return doc_ref[1].id
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            raise e
    
    async def get_document(self, collection: str, doc_id: str):
        """Get a document by ID"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"Error getting document: {str(e)}")
            raise e
    
    async def update_document(self, collection: str, doc_id: str, data: dict):
        """Update a document"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating document: {str(e)}")
            raise e
    
    async def delete_document(self, collection: str, doc_id: str):
        """Delete a document"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            raise e
    
    async def query_collection(self, collection: str, field: str, operator: str, value: any):
        """Query documents in a collection"""
        try:
            docs = self.db.collection(collection).where(field, operator, value).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error querying collection: {str(e)}")
            raise e

# Singleton instance
db = FirebaseDB()
