"""
Servicio para interactuar con la API de WhatsApp
"""
import logging
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
import hmac
import hashlib
import json

from app.config import settings
from app.utils.text import sanitize_data

logger = logging.getLogger(__name__)

def rate_limit(calls: int, period: int):
    """Decorador para rate limiting"""
    def decorator(func):
        calls_made = []
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = datetime.now()
            # Limpiar llamadas antiguas
            calls_made[:] = [t for t in calls_made if now - t < timedelta(seconds=period)]
            
            if len(calls_made) >= calls:
                # Esperar hasta que podamos hacer otra llamada
                wait_time = (calls_made[0] + timedelta(seconds=period) - now).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    
            result = await func(*args, **kwargs)
            calls_made.append(now)
            return result
            
        return wrapper
    return decorator

class WhatsAppService:
    """Servicio para interactuar con la API de WhatsApp"""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp"""
        self.api_url = "https://graph.facebook.com/v17.0"
        self.phone_number_id = settings.WHATSAPP_PHONE_ID
        self.access_token = settings.WHATSAPP_TOKEN
        self.webhook_secret = settings.WHATSAPP_WEBHOOK_SECRET
        
        # Cliente HTTP con retry
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            transport=httpx.AsyncHTTPTransport(retries=3)
        )
        
        # Verificar configuración
        if not self.phone_number_id or not self.access_token:
            logger.error("WhatsApp configuration missing")
            raise ValueError("WhatsApp phone ID and token are required")
            
        logger.info("WhatsApp service initialized successfully")
        
    def verify_webhook_signature(self, signature: str, payload: bytes) -> bool:
        """Verifica la firma del webhook"""
        if not self.webhook_secret:
            return True  # Si no hay secreto configurado, aceptar todo
            
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    @rate_limit(calls=30, period=60)  # 30 llamadas por minuto
    async def send_message(self, to: str, message: str, retry_count: int = 0) -> Dict[str, Any]:
        """
        Envía un mensaje de texto por WhatsApp
        
        Args:
            to: Número de teléfono destino
            message: Mensaje a enviar
            retry_count: Número de reintentos realizados
            
        Returns:
            Dict con la respuesta de la API
        """
        try:
            # Sanitizar mensaje
            safe_message = sanitize_data({'message': message})['message']
            
            # Preparar payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": safe_message}
            }
            
            # Log del request (sanitizado)
            logger.debug(f"WhatsApp API request to: {to[:6]}...")
            
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
            
            logger.info(f"Message sent successfully to {to[:6]}...")
            return response_data
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json()
            error_code = error_data.get('error', {}).get('code')
            
            if error_code in [4, 100, 613] and retry_count < 3:  # Códigos de error recuperables
                await asyncio.sleep(2 ** retry_count)  # Backoff exponencial
                return await self.send_message(to, message, retry_count + 1)
                
            logger.error(f"HTTP error sending WhatsApp message: {sanitize_data(error_data)}")
            raise WhatsAppError(f"HTTP error: {error_code}") from e
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            raise WhatsAppError("Failed to send message") from e
    
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
        if not self.client.is_closed:
            await self.client.aclose()

class WhatsAppError(Exception):
    """Excepción personalizada para errores de WhatsApp"""
    pass
