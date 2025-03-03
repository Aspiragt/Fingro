"""
Módulo para manejar la interacción con Firebase
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class FirebaseError(Exception):
    """Excepción personalizada para errores de Firebase"""
    pass

class FirebaseDB:
    """Maneja la interacción con Firebase y el caché local"""
    
    def __init__(self):
        """Inicializa el cliente de Firestore o un almacenamiento en memoria"""
        self.use_memory = True
        self.memory_db = {}
        self.cache = TTLCache(maxsize=1000, ttl=300)  # TTL de 5 minutos
        logger.info("Usando almacenamiento en memoria en lugar de Firebase")
    
    async def get_conversation_state(self, phone: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la conversación
        
        Args:
            phone: Número de teléfono del usuario
            
        Returns:
            Dict[str, Any]: Estado actual de la conversación y datos del usuario
        """
        # Intentar obtener desde el caché
        cache_key = f"conv_state_{phone}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Si no está en caché, obtener del almacenamiento en memoria
        collection_key = f"conversations_{phone}"
        if collection_key in self.memory_db:
            result = self.memory_db[collection_key]
            self.cache[cache_key] = result
            return result
        
        # Si no existe, crear un estado inicial
        initial_state = {
            "state": "start",
            "collected_data": {},
            "timestamp": datetime.now().isoformat()
        }
        self.memory_db[collection_key] = initial_state
        self.cache[cache_key] = initial_state
        return initial_state
    
    async def update_conversation_state(self, phone: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza el estado de una conversación
        
        Args:
            phone: Número de teléfono del usuario
            updates: Datos a actualizar
            
        Returns:
            Dict[str, Any]: Estado actualizado
        """
        try:
            # Obtener estado actual
            collection_key = f"conversations_{phone}"
            current_state = self.memory_db.get(collection_key, {})
            
            # Actualizar estado
            current_state.update(updates)
            current_state["timestamp"] = datetime.now().isoformat()
            
            # Guardar en memoria
            self.memory_db[collection_key] = current_state
            
            # Actualizar caché
            cache_key = f"conv_state_{phone}"
            self.cache[cache_key] = current_state
            
            return current_state
        except Exception as e:
            logger.error(f"Error actualizando estado: {str(e)}")
            raise FirebaseError(f"Error updating conversation state: {str(e)}")
    
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un documento
        
        Args:
            collection: Nombre de la colección
            doc_id: ID del documento
            
        Returns:
            Optional[Dict[str, Any]]: Documento o None si no existe
        """
        cache_key = f"{collection}_{doc_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        collection_key = f"{collection}_{doc_id}"
        doc = self.memory_db.get(collection_key)
        
        if doc:
            self.cache[cache_key] = doc
        
        return doc
    
    async def add_document(self, collection: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Agrega un documento a la colección
        
        Args:
            collection: Nombre de la colección
            data: Datos del documento
            doc_id: ID opcional del documento
            
        Returns:
            str: ID del documento creado
        """
        try:
            if not doc_id:
                import uuid
                doc_id = str(uuid.uuid4())
            
            data["created_at"] = datetime.now().isoformat()
            data["updated_at"] = data["created_at"]
            
            collection_key = f"{collection}_{doc_id}"
            self.memory_db[collection_key] = data
            
            # Actualizar caché
            cache_key = f"{collection}_{doc_id}"
            self.cache[cache_key] = data
            
            return doc_id
        except Exception as e:
            logger.error(f"Error agregando documento: {str(e)}")
            raise FirebaseError(f"Error adding document: {str(e)}")
    
    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Actualiza un documento existente
        
        Args:
            collection: Nombre de la colección
            doc_id: ID del documento
            data: Datos a actualizar
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            collection_key = f"{collection}_{doc_id}"
            current_doc = self.memory_db.get(collection_key)
            
            if not current_doc:
                return False
            
            # Actualizar documento
            data["updated_at"] = datetime.now().isoformat()
            current_doc.update(data)
            
            # Guardar en memoria
            self.memory_db[collection_key] = current_doc
            
            # Actualizar caché
            cache_key = f"{collection}_{doc_id}"
            self.cache[cache_key] = current_doc
            
            return True
        except Exception as e:
            logger.error(f"Error actualizando documento: {str(e)}")
            raise FirebaseError(f"Error updating document: {str(e)}")
    
    async def query_collection(self, collection: str, field: str, operator: str, value: Any) -> list[Dict[str, Any]]:
        """
        Consulta documentos en una colección
        
        Args:
            collection: Nombre de la colección
            field: Campo a comparar
            operator: Operador de comparación (==, >, <, >=, <=, !=)
            value: Valor a comparar
            
        Returns:
            list[Dict[str, Any]]: Lista de documentos que cumplen con la condición
        """
        try:
            result = []
            
            # Filtrar documentos en memoria
            for key, doc in self.memory_db.items():
                if key.startswith(f"{collection}_"):
                    if operator == "==":
                        if field in doc and doc[field] == value:
                            result.append(doc)
                    elif operator == ">":
                        if field in doc and doc[field] > value:
                            result.append(doc)
                    elif operator == "<":
                        if field in doc and doc[field] < value:
                            result.append(doc)
                    elif operator == ">=":
                        if field in doc and doc[field] >= value:
                            result.append(doc)
                    elif operator == "<=":
                        if field in doc and doc[field] <= value:
                            result.append(doc)
                    elif operator == "!=":
                        if field in doc and doc[field] != value:
                            result.append(doc)
            
            return result
        except Exception as e:
            logger.error(f"Error consultando colección: {str(e)}")
            raise FirebaseError(f"Error querying collection: {str(e)}")
    
    async def update_user_state(self, phone: str, user_data: Dict[str, Any]) -> None:
        """
        Actualiza el estado de un usuario, útil para la conversación
        
        Args:
            phone: Número de teléfono del usuario
            user_data: Nueva información del usuario
        """
        try:
            collection_key = f"user_state_{phone}"
            self.memory_db[collection_key] = user_data
            # Actualizar caché
            cache_key = f"user_{phone}"
            self.cache[cache_key] = user_data
        except Exception as e:
            logger.error(f"Error al actualizar estado del usuario {phone}: {e}")
            raise FirebaseError(f"Error al actualizar usuario: {e}")
    
    async def clear_user_cache(self, phone: str) -> None:
        """
        Limpia la caché y el estado del usuario para comenzar una conversación nueva
        
        Args:
            phone: Número de teléfono del usuario
        """
        try:
            # Eliminar del caché
            cache_key = f"user_{phone}"
            conv_cache_key = f"conv_state_{phone}"
            if cache_key in self.cache:
                del self.cache[cache_key]
            if conv_cache_key in self.cache:
                del self.cache[conv_cache_key]
            
            # Eliminar del almacenamiento en memoria
            collection_key = f"user_state_{phone}"
            conv_collection_key = f"conversations_{phone}"
            if collection_key in self.memory_db:
                del self.memory_db[collection_key]
            if conv_collection_key in self.memory_db:
                del self.memory_db[conv_collection_key]
                
            logger.info(f"Caché del usuario {phone} limpiada correctamente")
        except Exception as e:
            logger.error(f"Error al limpiar caché del usuario {phone}: {e}")
            # No lanzamos excepción para no interrumpir el flujo si hay error de caché

# Instancia global
firebase_manager = FirebaseDB()
