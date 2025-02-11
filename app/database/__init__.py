"""
Módulo para interacción con Firebase
"""
from typing import dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Inicializar Firebase
cred_path = os.getenv('FIREBASE_CREDENTIALS')
if cred_path:
    cred = credentials.Certificate(json.loads(cred_path))
else:
    cred = credentials.Certificate('firebase-credentials.json')

try:
    firebase_admin.initialize_app(cred)
except ValueError:
    # La app ya está inicializada
    pass

db = firestore.client()

__all__ = ['db']
