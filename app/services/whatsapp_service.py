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
        self.api_version = "v21.0"
        self.api_url = settings.WHATSAPP_API_URL
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_ID.strip()  # Asegurar que no hay espacios
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Validar configuración
        if not self.token:
            logger.error("WHATSAPP_ACCESS_TOKEN no está configurado")
            raise ValueError("WHATSAPP_ACCESS_TOKEN es requerido")
            
        if not self.phone_number_id:
            logger.error("WHATSAPP_PHONE_ID no está configurado")
            raise ValueError("WHATSAPP_PHONE_ID es requerido")
        
        logger.info(f"WhatsApp Service inicializado con:")
        logger.info(f"- API URL: {self.api_url}")
        logger.info(f"- API Version: {self.api_version}")
        logger.info(f"- Phone ID: {self.phone_number_id}")
        logger.info(f"- Token length: {len(self.token)} caracteres")
    
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
            # Asegurar que el número no tenga el símbolo + y esté limpio
            to = to.lstrip("+").strip()
            
            url = f"{self.api_url}/{self.api_version}/{self.phone_number_id}/messages"
            logger.info(f"Enviando mensaje a URL: {url}")
            
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
                    "preview_url": False,
                    "body": message
                }
            }
            
            logger.info(f"Request data: {data}")
            response = await self.client.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"Error HTTP {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return False
                
            response_data = response.json()
            logger.info(f"Respuesta de WhatsApp: {response_data}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando mensaje a {to}: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response content: {e.response.text}")
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
            url = f"{self.api_url}/{self.api_version}/{self.phone_number_id}/messages"
            logger.info(f"Enviando plantilla a URL: {url}")
            
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
            
            logger.info(f"Request data: {data}")
            response = await self.client.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"Error HTTP {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return False
                
            response_data = response.json()
            logger.info(f"Respuesta de WhatsApp: {response_data}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando plantilla {template_name} a {to}: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response content: {e.response.text}")
            return False
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()

# No crear instancia global aquí, se crea en main.py
