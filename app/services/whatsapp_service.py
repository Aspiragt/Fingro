"""
Módulo para manejar la interacción con la API de WhatsApp
"""
import logging
from typing import Dict, Any, List, Tuple, Optional
import httpx
from app.config import settings
from app.chat.conversation_flow import conversation_manager
from app.database.firebase import firebase_manager
from app.utils.constants import MESSAGES

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Servicio para interactuar con la API de WhatsApp"""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp"""
        self.api_url = settings.WHATSAPP_API_URL
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def handle_webhook(self, data: Dict[str, Any]) -> None:
        """
        Maneja los webhooks entrantes de WhatsApp
        """
        try:
            # Extraer datos del mensaje
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            if 'messages' in value:
                message = value['messages'][0]
                phone = message['from']
                
                # Extraer el nombre del contacto si está disponible
                name = None
                if 'contacts' in value:
                    contact = value['contacts'][0]
                    name = contact.get('profile', {}).get('name')
                    if name:
                        await firebase_manager.update_user_name(phone, name)
                
                # Procesar el mensaje según su tipo
                if message['type'] == 'text':
                    text = message['text']['body'].strip().lower()
                    
                    # Manejar comandos especiales
                    if text == 'reiniciar':
                        await firebase_manager.reset_user_state(phone)
                        await self.send_message(phone, MESSAGES['welcome'])
                        return
                        
                    try:
                        # Procesar el mensaje normal
                        response = await conversation_manager.handle_message(phone, text)
                        
                        # Enviar respuesta
                        if isinstance(response, tuple):
                            message, attachments = response
                            await self.send_message(phone, message)
                            if attachments:
                                for attachment in attachments:
                                    await self.send_attachment(phone, attachment)
                        else:
                            await self.send_message(phone, response)
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        await self.send_message(phone, MESSAGES['error'])
                        
                elif message['type'] in ['image', 'document', 'video']:
                    await self.send_message(
                        phone,
                        "Lo siento, por el momento solo puedo procesar mensajes de texto. "
                        "Por favor, escribe tu mensaje."
                    )
                    
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            
    async def send_message(self, to: str, message: str) -> bool:
        """
        Envía un mensaje de texto a través de WhatsApp
        
        Args:
            to: Número de teléfono del destinatario
            message: Mensaje a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            async with self.client as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
            
    async def send_attachment(self, to: str, attachment: Dict[str, str]) -> bool:
        """
        Envía un archivo adjunto a través de WhatsApp
        
        Args:
            to: Número de teléfono del destinatario
            attachment: Diccionario con tipo y URL del archivo
            
        Returns:
            bool: True si el archivo se envió correctamente
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": attachment['type'],
                attachment['type']: {"link": attachment['url']}
            }
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            async with self.client as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Error sending attachment: {str(e)}")
            return False

# Instancia global
whatsapp_service = WhatsAppService()
