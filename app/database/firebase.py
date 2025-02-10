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
            # Try to get credentials from environment variable
            cred_dict = os.getenv('FIREBASE_CREDENTIALS')
            if cred_dict:
                cred = credentials.Certificate(json.loads(cred_dict))
            else:
                # Fallback to credentials file
                cred_path = Path(__file__).parent.parent.parent / 'firebase-credentials.json'
                cred = credentials.Certificate(str(cred_path))
            
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
            print(f"\n=== AGREGANDO DOCUMENTO ===")
            print(f"Colección: {collection}")
            print(f"ID: {doc_id if doc_id else 'auto-generated'}")
            print(f"Datos: {json.dumps(data, indent=2)}")
            
            if doc_id:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.set(data)
                print(f"Documento creado con ID: {doc_id}")
                return doc_id
            else:
                doc_ref = self.db.collection(collection).add(data)[1]
                print(f"Documento creado con ID: {doc_ref.id}")
                return doc_ref.id
                
        except Exception as e:
            print(f"Error agregando documento: {str(e)}")
            raise e
    
    async def get_document(self, collection: str, doc_id: str):
        """Get a document by ID"""
        try:
            print(f"\n=== OBTENIENDO DOCUMENTO ===")
            print(f"Colección: {collection}")
            print(f"ID: {doc_id}")
            
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                print(f"Documento encontrado: {json.dumps(data, indent=2)}")
                return data
            else:
                print("Documento no encontrado")
                return None
                
        except Exception as e:
            print(f"Error obteniendo documento: {str(e)}")
            raise e
    
    async def update_document(self, collection: str, doc_id: str, data: dict):
        """Update a document"""
        try:
            print(f"\n=== ACTUALIZANDO DOCUMENTO ===")
            print(f"Colección: {collection}")
            print(f"ID: {doc_id}")
            print(f"Datos: {json.dumps(data, indent=2)}")
            
            doc_ref = self.db.collection(collection).document(doc_id)
            
            # Verificar si el documento existe
            doc = doc_ref.get()
            if not doc.exists:
                print(f"Error: Documento {doc_id} no existe")
                raise ValueError(f"Document {doc_id} does not exist")
            
            doc_ref.update(data)
            print("Documento actualizado exitosamente")
            return True
            
        except Exception as e:
            print(f"Error actualizando documento: {str(e)}")
            raise e
    
    async def delete_document(self, collection: str, doc_id: str):
        """Delete a document"""
        try:
            print(f"\n=== ELIMINANDO DOCUMENTO ===")
            print(f"Colección: {collection}")
            print(f"ID: {doc_id}")
            
            doc_ref = self.db.collection(collection).document(doc_id)
            
            # Verificar si el documento existe
            doc = doc_ref.get()
            if not doc.exists:
                print(f"Error: Documento {doc_id} no existe")
                raise ValueError(f"Document {doc_id} does not exist")
            
            doc_ref.delete()
            print("Documento eliminado exitosamente")
            return True
            
        except Exception as e:
            print(f"Error eliminando documento: {str(e)}")
            raise e
    
    async def query_collection(self, collection: str, field: str, operator: str, value: any):
        """Query documents in a collection"""
        try:
            print(f"\n=== CONSULTANDO COLECCIÓN ===")
            print(f"Colección: {collection}")
            print(f"Campo: {field}")
            print(f"Operador: {operator}")
            print(f"Valor: {value}")
            
            docs = self.db.collection(collection).where(field, operator, value).stream()
            results = [doc.to_dict() for doc in docs]
            
            print(f"Documentos encontrados: {len(results)}")
            for doc in results:
                print(f"- {json.dumps(doc, indent=2)}")
            
            return results
            
        except Exception as e:
            print(f"Error consultando colección: {str(e)}")
            raise e

# Singleton instance
db = FirebaseDB()
