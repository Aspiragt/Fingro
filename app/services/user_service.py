from typing import Optional, Dict
from datetime import datetime
import uuid
import json
from app.database.firebase import db
from app.models.user import User

class UserService:
    def __init__(self):
        self.db = db
    
    async def get_or_create_user(self, phone_number: str) -> User:
        """Get an existing user by phone number or create a new one"""
        print(f"\n=== BUSCANDO/CREANDO USUARIO ===")
        print(f"Número de teléfono: {phone_number}")
        
        # Try to find existing user
        users = await self.db.query_collection('users', 'phone_number', '==', phone_number)
        
        if users:
            user = User(**users[0])
            print(f"Usuario existente encontrado:")
            print(f"ID: {user.id}")
            print(f"Nombre: {user.name}")
            print(f"Datos: {json.dumps(user.model_dump(), indent=2)}")
            return user
        
        # Create new user if not found
        user_id = str(uuid.uuid4())
        now = datetime.now()
        
        user = User(
            id=user_id,
            phone_number=phone_number,
            created_at=now,
            updated_at=now
        )
        
        print(f"Creando nuevo usuario:")
        print(f"ID: {user.id}")
        print(f"Datos: {json.dumps(user.model_dump(), indent=2)}")
        
        await self.db.add_document('users', user.model_dump(), user.id)
        return user
    
    async def update_user(self, user_id: str, updates: Dict) -> User:
        """Update user data"""
        print(f"\n=== ACTUALIZANDO USUARIO ===")
        print(f"ID: {user_id}")
        print(f"Actualizaciones: {json.dumps(updates, indent=2)}")
        
        # Get current user data
        user_data = await self.db.get_document('users', user_id)
        if not user_data:
            print(f"Error: Usuario {user_id} no encontrado")
            raise ValueError(f"User {user_id} not found")
        
        # Update user object
        user = User(**user_data)
        old_data = user.model_dump()
        
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        
        print(f"Datos anteriores: {json.dumps(old_data, indent=2)}")
        print(f"Nuevos datos: {json.dumps(user.model_dump(), indent=2)}")
        
        # Save to database
        await self.db.update_document('users', user_id, user.model_dump())
        return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        print(f"\n=== OBTENIENDO USUARIO ===")
        print(f"ID: {user_id}")
        
        user_data = await self.db.get_document('users', user_id)
        if user_data:
            user = User(**user_data)
            print(f"Usuario encontrado:")
            print(f"ID: {user.id}")
            print(f"Nombre: {user.name}")
            print(f"Datos: {json.dumps(user.model_dump(), indent=2)}")
            return user
        
        print("Usuario no encontrado")
        return None
    
    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        print(f"\n=== BUSCANDO USUARIO POR TELÉFONO ===")
        print(f"Número: {phone_number}")
        
        users = await self.db.query_collection('users', 'phone_number', '==', phone_number)
        if users:
            user = User(**users[0])
            print(f"Usuario encontrado:")
            print(f"ID: {user.id}")
            print(f"Nombre: {user.name}")
            print(f"Datos: {json.dumps(user.model_dump(), indent=2)}")
            return user
        
        print("Usuario no encontrado")
        return None
