import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener ruta de credenciales
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
print(f"Ruta de credenciales: {cred_path}")

try:
    # Inicializar Firebase
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase inicializado correctamente")
    
    # Intentar una operación simple
    usuarios = db.collection("conversations").get()
    print(f"✅ Conexión a Firestore exitosa. Documentos encontrados: {len(list(usuarios))}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
