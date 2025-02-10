from app.models.user import User
from app.database.firebase import db
from datetime import datetime
import uuid

class UserService:
    def __init__(self):
        self.db = db
    
    async def get_or_create_user(self, phone_number: str) -> User:
        """Get a user by phone number or create if not exists"""
        try:
            print(f"\n=== BUSCANDO O CREANDO USUARIO ===")
            print(f"Teléfono: {phone_number}")
            
            # Buscar usuario existente
            users = await self.db.query_collection('users', 'phone_number', '==', phone_number)
            
            if users and len(users) > 0:
                print("Usuario encontrado")
                # Usuario existe, convertir a modelo
                user_data = users[0]
                
                # Convertir strings ISO a datetime
                if isinstance(user_data.get('created_at'), str):
                    user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                if isinstance(user_data.get('updated_at'), str):
                    user_data['updated_at'] = datetime.fromisoformat(user_data['updated_at'])
                
                user = User(**user_data)
                print(f"Usuario: {user.model_dump_json(indent=2)}")
                return user
            
            print("Usuario no encontrado, creando nuevo")
            
            # Generar ID único
            user_id = str(uuid.uuid4())
            
            # Crear datos del usuario
            user_data = {
                'id': user_id,
                'phone_number': phone_number,
                'name': '',
                'country': '',
                'location': '',
                'crops': [],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Guardar en Firebase usando el ID generado
            saved_data = await self.db.add_document('users', user_data, user_id)
            
            # Convertir a modelo
            user = User(**saved_data)
            print(f"Usuario creado: {user.model_dump_json(indent=2)}")
            return user
            
        except Exception as e:
            print(f"Error en get_or_create_user: {str(e)}")
            import traceback
            print(traceback.format_exc())
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

    async def delete_user_data(self, phone_number: str) -> bool:
        """Delete a user and all associated data"""
        try:
            print(f"\n=== ELIMINANDO DATOS DE USUARIO ===")
            print(f"Teléfono: {phone_number}")
            
            # 1. Buscar usuario por número de teléfono
            users = await self.db.query_collection(
                'users',
                'phone_number',
                '==',
                phone_number
            )
            
            if not users:
                print("No se encontró el usuario")
                return True
                
            user_data = users[0]
            user_id = user_data.get('id')
            
            print(f"Usuario encontrado: {user_id}")
            
            # 2. Buscar conversaciones del usuario
            convs = await self.db.query_collection(
                'conversations',
                'user_id',
                '==',
                user_id
            )
            
            # 3. Eliminar conversaciones
            for conv in convs:
                conv_id = conv.get('id')
                print(f"Eliminando conversación: {conv_id}")
                await self.db.delete_document('conversations', conv_id)
            
            # 4. Eliminar usuario
            print(f"Eliminando usuario: {user_id}")
            await self.db.delete_document('users', user_id)
            
            print("Datos eliminados exitosamente")
            return True
            
        except Exception as e:
            print(f"Error eliminando datos de usuario: {str(e)}")
            raise e
