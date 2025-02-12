"""
Modelos para conversaciones
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.utils.constants import ConversationState

class Message(BaseModel):
    """Modelo para mensajes"""
    role: str  # user o assistant
    content: str
    original_content: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class ConversationContext(BaseModel):
    """Contexto de la conversación"""
    state: ConversationState = ConversationState.INITIAL
    collected_data: Dict[str, Any] = {}
    validation_errors: List[str] = []
    retry_count: int = 0
    last_message_timestamp: Optional[datetime] = None

class Conversation(BaseModel):
    """Modelo de conversación"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    user_id: str
    messages: List[Message] = []
    context: ConversationContext = ConversationContext()
    active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def add_message(self, role: str, content: str, original_content: Optional[str] = None) -> None:
        """Agrega un mensaje a la conversación"""
        self.messages.append(
            Message(
                role=role,
                content=content,
                original_content=original_content,
                timestamp=datetime.now()
            )
        )
        self.updated_at = datetime.now()
    
    def update_state(self, new_state: ConversationState) -> None:
        """Actualiza el estado de la conversación"""
        self.context.state = new_state
        self.context.last_message_timestamp = datetime.now()
        self.updated_at = datetime.now()
    
    def update_data(self, key: str, value: Any) -> None:
        """Actualiza los datos recolectados"""
        self.context.collected_data[key] = value
        self.updated_at = datetime.now()
    
    def add_validation_error(self, error: str) -> None:
        """Agrega un error de validación"""
        self.context.validation_errors.append(error)
        self.context.retry_count += 1
        self.updated_at = datetime.now()
    
    def clear_validation_errors(self) -> None:
        """Limpia los errores de validación"""
        self.context.validation_errors = []
        self.context.retry_count = 0
        self.updated_at = datetime.now()
    
    def get_last_message(self) -> Optional[Message]:
        """Obtiene el último mensaje"""
        if self.messages:
            return self.messages[-1]
        return None
    
    def get_data(self, key: str) -> Optional[Any]:
        """Obtiene un dato específico"""
        return self.context.collected_data.get(key)
    
    def has_data(self, key: str) -> bool:
        """Verifica si existe un dato"""
        return key in self.context.collected_data
    
    def reset(self) -> None:
        """Reinicia la conversación"""
        self.context = ConversationContext()
        self.messages = []
        self.active = True
        self.updated_at = datetime.now()
