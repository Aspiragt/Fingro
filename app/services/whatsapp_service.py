from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime, timedelta
from app.utils.exceptions import WhatsAppAPIError, WhatsAppTemplateError, FirebaseError
from app.utils.text_processing import normalize_text, calculate_text_similarity
import httpx
import os
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, firebase_db):
        """Initialize WhatsApp service with Firebase connection"""
        self.firebase_db = firebase_db
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

    async def _get_or_create_user(self, phone_number: str) -> Dict[str, Any]:
        """Get or create user with caching"""
        try:
            # Intentar obtener de caché
            if phone_number in self.user_cache:
                return self.user_cache[phone_number]
            
            # Obtener de Firebase
            user = self.firebase_db.get_user(phone_number)
            if not user:
                # Crear nuevo usuario
                user = {
                    "phone_number": phone_number,
                    "created_at": datetime.now().isoformat(),
                    "last_interaction": datetime.now().isoformat(),
                    "conversation_state": "START",
                    "data": {}
                }
                self.firebase_db.create_user(phone_number, user)
            
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
                
            if response.status_code != 200:
                raise WhatsAppAPIError(
                    f"Error sending message: {response.text}",
                    status_code=response.status_code,
                    response=response.json()
                )
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise WhatsAppAPIError(f"Failed to send message: {str(e)}")

    async def send_template_message(self, to_number: str, template_name: str, 
                                 language_code: str = "es", components: list = None) -> Dict[str, Any]:
        """Send template message to WhatsApp"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            async with self.client as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
            if response.status_code != 200:
                raise WhatsAppTemplateError(
                    f"Error sending template: {response.text}",
                    status_code=response.status_code,
                    response=response.json()
                )
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Error sending template: {str(e)}")
            raise WhatsAppTemplateError(f"Failed to send template: {str(e)}")

    async def _handle_text_message(self, user: Dict[str, Any], message_data: Dict[str, Any]) -> None:
        """Handle text message"""
        text = message_data.get("text", "")
        state = user.get("conversation_state", "START")
        
        # Obtener respuesta del caché si existe
        cache_key = f"{state}:{normalize_text(text)}"
        if cache_key in self.response_cache:
            response = self.response_cache[cache_key]
        else:
            # Procesar mensaje según el estado
            response = await self._get_response_based_on_state(user, text)
            # Guardar en caché
            self.response_cache[cache_key] = response
        
        # Enviar respuesta
        await self.send_text_message(user["phone_number"], response)
        
        # Actualizar estado del usuario
        self._update_user_state(user, text)

    async def _handle_location_message(self, user: Dict[str, Any], message_data: Dict[str, Any]) -> None:
        """Handle location message"""
        location = message_data.get("location", {})
        if location:
            # Guardar ubicación
            user["data"]["location"] = {
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "timestamp": datetime.now().isoformat()
            }
            self.firebase_db.update_user(user["phone_number"], user)
            
            # Enviar confirmación
            await self.send_text_message(
                user["phone_number"],
                "¡Gracias por compartir tu ubicación! Esto nos ayudará a brindarte un mejor servicio."
            )

    async def _handle_interactive_message(self, user: Dict[str, Any], message_data: Dict[str, Any]) -> None:
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
        """Handle errors gracefully"""
        try:
            error_message = "Lo siento, ha ocurrido un error. Por favor, intenta nuevamente en unos momentos."
            await self.send_text_message(phone_number, error_message)
        except:
            logger.error("Failed to send error message to user")

    def _update_user_state(self, user: Dict[str, Any], message: str) -> None:
        """Update user state based on message"""
        try:
            user["last_interaction"] = datetime.now().isoformat()
            # Actualizar estado según el flujo de conversación
            # TODO: Implementar lógica de estados
            self.firebase_db.update_user(user["phone_number"], user)
            self.user_cache[user["phone_number"]] = user
        except Exception as e:
            logger.error(f"Error updating user state: {str(e)}")

    async def _get_response_based_on_state(self, user: Dict[str, Any], message: str) -> str:
        """Get response based on user state and message"""
        state = user.get("conversation_state", "START")
        
        # TODO: Implementar lógica de respuestas según estado
        return "Gracias por tu mensaje. Pronto implementaremos más funcionalidades."
