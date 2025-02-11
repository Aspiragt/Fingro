"""
Módulo para manejar la interacción con la API de WhatsApp
"""
import logging
from typing import Dict, Any, List
import httpx
from app.config import settings
from app.chat.conversation_flow import conversation_manager
from app.database.firebase import firebase_manager

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Servicio para interactuar con la API de WhatsApp"""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp"""
        self.api_url = settings.WHATSAPP_API_URL
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        
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
                if 'contacts' in value:
                    contact = value['contacts'][0]
                    name = contact.get('profile', {}).get('name')
                    if name:
                        firebase_manager.update_user_name(phone, name)
                
                # Procesar el mensaje
                if message['type'] == 'text':
                    text = message['text']['body']
                    response, attachments = conversation_manager.handle_message(phone, text)
                    
                    # Enviar respuesta
                    await self.send_message(phone, response)
                    
                    # Enviar archivos adjuntos si hay
                    for attachment in attachments:
                        await self.send_file(phone, attachment)
                        
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
    
    async def send_message(self, to: str, message: str) -> None:
        """
        Envía un mensaje de texto por WhatsApp
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/{self.phone_number_id}/messages",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error enviando mensaje: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
    
    async def send_file(self, to: str, file_url: str, caption: str = None) -> None:
        """
        Envía un archivo por WhatsApp
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "document",
                "document": {
                    "link": file_url,
                    "caption": caption if caption else ""
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/{self.phone_number_id}/messages",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error enviando archivo: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error enviando archivo: {str(e)}")

    async def send_template(self, to: str, template_name: str, components: List[Dict[str, Any]] = None) -> None:
        """
        Envía un mensaje usando una plantilla de WhatsApp
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "es"
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/{self.phone_number_id}/messages",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error enviando template: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error enviando template: {str(e)}")

# Instancia global
whatsapp_service = WhatsAppService()
