from typing import Any, Optional, Dict
import logging
from datetime import datetime
from app.utils.exceptions import WhatsAppAPIError, FirebaseError
from app.utils.constants import ConversationState, MESSAGES
from app.models.user import User, ConversationState as UserConversationState
from app.database.firebase import FirebaseDB
import httpx
import os
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        """Initialize WhatsApp service"""
        self.firebase_db = FirebaseDB()
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        
        if not self.phone_number_id or not self.access_token:
            raise ValueError("WhatsApp credentials not properly configured")
            
        self.base_url = "https://graph.facebook.com/v17.0"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Cache para almacenar respuestas frecuentes (5 minutos de TTL)
        self.response_cache = TTLCache(maxsize=100, ttl=300)
        
        # Cache para almacenar datos de usuario (1 hora de TTL)
        self.user_cache = TTLCache(maxsize=1000, ttl=3600)
        
        # Cliente HTTP con timeout y reintentos
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def process_message(self, from_number: str, message_data: Dict[str, Any]) -> None:
        """Process incoming WhatsApp message"""
        try:
            # Comando especial para reiniciar
            if message_data.get("type") == "text" and message_data["text"]["body"].lower() == "reiniciar":
                self.firebase_db.reset_conversation(from_number)
                await self.send_text_message(from_number, MESSAGES["welcome"])
                return

            # Obtener o crear usuario
            user = await self._get_or_create_user(from_number)
            
            # Procesar el mensaje según su tipo
            if message_data["type"] == "text":
                await self._handle_text_message(user, message_data)
            elif message_data["type"] == "location":
                await self._handle_location_message(user, message_data)
            elif message_data["type"] == "interactive":
                await self._handle_interactive_message(user, message_data)
            else:
                await self.send_text_message(
                    from_number,
                    "Lo siento, por ahora solo puedo procesar mensajes de texto, ubicación o botones."
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self._handle_error(from_number, e)

    async def _get_or_create_user(self, phone_number: str) -> User:
        """Get or create user with caching"""
        try:
            # Intentar obtener de caché
            if phone_number in self.user_cache:
                return self.user_cache[phone_number]
            
            # Obtener de Firebase
            user_data = self.firebase_db.get_user(phone_number)
            if not user_data:
                # Crear nuevo usuario
                user = User(
                    phone_number=phone_number,
                    conversation_state=UserConversationState(
                        state=ConversationState.START
                    )
                )
                self.firebase_db.create_user(phone_number, user.dict())
            else:
                user = User(**user_data)
            
            # Actualizar caché
            self.user_cache[phone_number] = user
            return user
            
        except Exception as e:
            raise FirebaseError(f"Error getting/creating user: {str(e)}")

    async def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send text message to WhatsApp"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "text",
                "text": {"body": message}
            }
            
            async with self.client as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise WhatsAppAPIError(f"Error sending message: {str(e)}")

    async def _handle_text_message(self, user: User, message_data: Dict[str, Any]) -> None:
        """Handle text message"""
        text = message_data["text"]["body"]
        state = user.conversation_state.state
        
        # Actualizar datos según el estado
        if state == ConversationState.ASKING_CROP:
            user.crops.append(text)
            user.conversation_state.state = ConversationState.ASKING_AREA
        elif state == ConversationState.ASKING_AREA:
            user.conversation_state.collected_data["area"] = text
            user.conversation_state.state = ConversationState.ASKING_IRRIGATION
        # ... más estados ...
        
        # Guardar cambios
        self.firebase_db.update_user(user.phone_number, user.dict())
        
        # Enviar siguiente mensaje
        await self.send_text_message(user.phone_number, MESSAGES[user.conversation_state.state.value])

    async def _handle_location_message(self, user: User, message_data: Dict[str, Any]) -> None:
        """Handle location message"""
        if user.conversation_state.state == ConversationState.WAITING_LOCATION:
            user.location = {
                "latitude": message_data["location"]["latitude"],
                "longitude": message_data["location"]["longitude"],
                "timestamp": datetime.now()
            }
            user.conversation_state.state = ConversationState.ASKING_CROP
            
            # Guardar cambios
            self.firebase_db.update_user(user.phone_number, user.dict())
            
            # Enviar siguiente mensaje
            await self.send_text_message(user.phone_number, MESSAGES["crop_request"])

    async def _handle_interactive_message(self, user: User, message_data: Dict[str, Any]) -> None:
        """Handle interactive message (buttons/list)"""
        interactive = message_data.get("interactive", {})
        if interactive:
            response_type = interactive.get("type")
            if response_type == "button_reply":
                button_id = interactive["button_reply"]["id"]
                await self._handle_button_response(user, button_id)
            elif response_type == "list_reply":
                list_id = interactive["list_reply"]["id"]
                await self._handle_list_response(user, list_id)

    async def _handle_error(self, phone_number: str, error: Exception) -> None:
        """Handle error in message processing"""
        error_message = MESSAGES.get("error", "Lo siento, ha ocurrido un error. Por favor escribe 'reiniciar' para comenzar de nuevo.")
        await self.send_text_message(phone_number, error_message)
        logger.error(f"Error processing message for {phone_number}: {str(error)}")

    async def _handle_button_response(self, user: User, button_id: str) -> None:
        """Handle button response"""
        # TODO: Implementar lógica para manejar respuestas de botones
        pass

    async def _handle_list_response(self, user: User, list_id: str) -> None:
        """Handle list response"""
        # TODO: Implementar lógica para manejar respuestas de listas
        pass
