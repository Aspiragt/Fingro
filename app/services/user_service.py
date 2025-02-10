from app.models.user import User
from app.database.firebase import db
from datetime import datetime

class UserService:
    def __init__(self):
        self.db = db
    
    async def get_or_create_user(self, phone_number: str) -> User:
        """Get a user by phone number or create if not exists"""
        try:
            # Buscar usuario existente
            users = await self.db.query_collection('users', 'phone_number', '==', phone_number)
            
            if users and len(users) > 0:
                # Usuario existe, convertir a modelo
                user_data = users[0]
                user_data['id'] = user_data.get('id', '')  # Asegurar que id existe
                
                # Convertir strings ISO a datetime
                if isinstance(user_data.get('created_at'), str):
                    user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                if isinstance(user_data.get('updated_at'), str):
                    user_data['updated_at'] = datetime.fromisoformat(user_data['updated_at'])
                
                return User(**user_data)
            
            # Crear nuevo usuario
            user = User(
                id='',  # Se actualizará después
                phone_number=phone_number,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Guardar en Firebase
            user_dict = user.model_dump()
            doc_id = await self.db.add_document('users', user_dict)
            
            # Actualizar ID
            user.id = doc_id
            await self.db.update_document('users', doc_id, {'id': doc_id})
            
            return user
            
        except Exception as e:
            print(f"Error en get_or_create_user: {str(e)}")
            raise e
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get a user by ID"""
        try:
            user_data = await self.db.get_document('users', user_id)
            if not user_data:
                return None
                
            # Convertir strings ISO a datetime
            if isinstance(user_data.get('created_at'), str):
                user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
            if isinstance(user_data.get('updated_at'), str):
                user_data['updated_at'] = datetime.fromisoformat(user_data['updated_at'])
            
            return User(**user_data)
            
        except Exception as e:
            print(f"Error en get_user_by_id: {str(e)}")
            raise e
    
    async def update_user(self, user: User) -> bool:
        """Update user data"""
        try:
            user.updated_at = datetime.now()
            user_dict = user.model_dump()
            
            await self.db.update_document('users', user.id, user_dict)
            return True
            
        except Exception as e:
            print(f"Error en update_user: {str(e)}")
            raise e
