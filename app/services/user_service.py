from typing import Dict, Any
from datetime import datetime
import uuid
from app.database.firebase import db
from app.models.user import User

class UserService:
    def __init__(self):
        self.db = db
    
    async def get_or_create_user(self, phone_number: str) -> User:
        """Get existing user or create a new one"""
        print(f"\n=== OBTENIENDO/CREANDO USUARIO ===")
        print(f"Teléfono: {phone_number}")
        
        # Buscar usuario existente
        users = await self.db.query_collection('users', 'phone_number', '==', phone_number)
        
        if users:
            user = User(**users[0])
            print(f"Usuario existente encontrado: {user.model_dump_json(indent=2)}")
            return user
        
        # Crear nuevo usuario
        user = User(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        print(f"Creando nuevo usuario: {user.model_dump_json(indent=2)}")
        await self.db.add_document('users', user.model_dump(), user.id)
        return user
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> None:
        """Update user data"""
        print(f"\n=== ACTUALIZANDO USUARIO ===")
        print(f"ID: {user_id}")
        print(f"Updates: {updates}")
        
        updates['updated_at'] = datetime.now()
        await self.db.update_document('users', user_id, updates)
        print("Usuario actualizado exitosamente")
