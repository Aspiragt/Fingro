"""
Módulo para manejar la interacción con la API de WhatsApp
"""
import logging
from typing import Dict, Any, List, Tuple, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Servicio para interactuar con la API de WhatsApp"""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp"""
        self.api_url = settings.WHATSAPP_API_URL
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_ID
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(self, to: str, message: str) -> bool:
        """
        Envía un mensaje de WhatsApp
        
        Args:
            to: Número de teléfono del destinatario
            message: Mensaje a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente
        """
        try:
            url = f"{self.api_url}/v17.0/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = await self.client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            logger.info(f"Mensaje enviado a {to}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando mensaje a {to}: {str(e)}")
            return False
    
    async def send_template(self, to: str, template_name: str, language: str = "es", components: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Envía un mensaje de plantilla de WhatsApp
        
        Args:
            to: Número de teléfono del destinatario
            template_name: Nombre de la plantilla
            language: Código de idioma (default: "es")
            components: Componentes de la plantilla (opcional)
            
        Returns:
            bool: True si el mensaje se envió correctamente
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language
                    }
                }
            }
            
            if components:
                data["template"]["components"] = components
            
            response = await self.client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            logger.info(f"Plantilla {template_name} enviada a {to}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando plantilla {template_name} a {to}: {str(e)}")
            return False
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()

# No crear instancia global aquí, se crea en main.py
