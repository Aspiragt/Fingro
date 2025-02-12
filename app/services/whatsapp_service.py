"""
Servicio para interactuar con la API de WhatsApp
"""
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Servicio para interactuar con la API de WhatsApp"""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp"""
        self.api_url = "https://graph.facebook.com/v17.0"
        self.phone_number_id = settings.WHATSAPP_PHONE_ID
        self.access_token = settings.WHATSAPP_TOKEN
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Verificar configuración
        if not self.phone_number_id or not self.access_token:
            logger.error("WhatsApp configuration missing")
            raise ValueError("WhatsApp phone ID and token are required")
            
        logger.info("WhatsApp service initialized successfully")
    
    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Envía un mensaje de texto por WhatsApp
        
        Args:
            to: Número de teléfono destino
            message: Mensaje a enviar
            
        Returns:
            Dict con la respuesta de la API
        """
        try:
            logger.info(f"Sending message to {to}: {message[:50]}...")
            
            # Preparar payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            # Log del request
            logger.debug(f"WhatsApp API request - URL: {self.api_url}/{self.phone_number_id}/messages")
            logger.debug(f"WhatsApp API request - Payload: {payload}")
            
            # Enviar mensaje
            response = await self.client.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Verificar respuesta
            response.raise_for_status()
            response_data = response.json()
            
            logger.info(f"Message sent successfully to {to}")
            logger.debug(f"WhatsApp API response: {response_data}")
            
            return response_data
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error sending WhatsApp message: {str(e.response.json())}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except httpx.RequestError as e:
            error_msg = f"Error sending WhatsApp message: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error sending WhatsApp message: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        finally:
            # Asegurar que el cliente se cierre
            if not self.client.is_closed:
                await self.client.aclose()
    
    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "es",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Envía un mensaje usando una plantilla
        
        Args:
            to: Número de teléfono destino
            template_name: Nombre de la plantilla
            language_code: Código de idioma
            components: Componentes de la plantilla
            
        Returns:
            Dict con la respuesta de la API
        """
        try:
            # Preparar payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            # Agregar componentes si existen
            if components:
                payload["template"]["components"] = components
            
            # Enviar mensaje
            response = await self.client.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Validar respuesta
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Error enviando template: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
            
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise
    
    async def send_interactive(
        self,
        to: str,
        interactive_type: str,
        header: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        footer: Optional[Dict[str, Any]] = None,
        action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envía un mensaje interactivo
        
        Args:
            to: Número de teléfono destino
            interactive_type: Tipo de mensaje interactivo
            header: Encabezado opcional
            body: Cuerpo opcional
            footer: Pie opcional
            action: Acción opcional
            
        Returns:
            Dict con la respuesta de la API
        """
        try:
            # Preparar payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": interactive_type
                }
            }
            
            # Agregar componentes opcionales
            if header:
                payload["interactive"]["header"] = header
            if body:
                payload["interactive"]["body"] = body
            if footer:
                payload["interactive"]["footer"] = footer
            if action:
                payload["interactive"]["action"] = action
            
            # Enviar mensaje
            response = await self.client.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Validar respuesta
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Error enviando mensaje interactivo: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
            
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
