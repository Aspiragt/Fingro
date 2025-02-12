"""
Servicio para interactuar con la API de WhatsApp
"""
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config import settings
from app.chat.conversation_flow import conversation_flow
from app.database.firebase import firebase_manager

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Servicio para interactuar con la API de WhatsApp"""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp"""
        self.api_url = "https://graph.facebook.com/v17.0"
        self.phone_number_id = settings.WHATSAPP_PHONE_ID
        self.access_token = settings.WHATSAPP_TOKEN
        self.client = httpx.AsyncClient(timeout=30.0)
    
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
            # Preparar payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
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
            logger.error(f"Error enviando mensaje: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
            
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise
    
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
    
    async def process_message(self, from_number: str, message: Dict[str, Any]) -> None:
        """
        Procesa un mensaje entrante de WhatsApp
        
        Args:
            from_number: Número de teléfono del remitente
            message: Datos del mensaje
        """
        try:
            # Extraer texto del mensaje
            if message.get("type") != "text":
                await self.send_message(
                    from_number,
                    "❌ Por favor, envía solo mensajes de texto."
                )
                return
            
            text = message.get("text", {}).get("body", "").strip()
            if not text:
                return
            
            # Obtener estado actual
            state_data = await firebase_manager.get_conversation_state(from_number)
            current_state = state_data.get("state", conversation_flow.STATES["START"])
            user_data = state_data.get("data", {})
            
            # Manejar comando de reinicio
            if text.lower() == "reiniciar":
                await firebase_manager.reset_user_state(from_number)
                await self.send_message(from_number, conversation_flow.get_welcome_message())
                return
            
            # Manejar comando para analizar otro cultivo
            if text.lower() == "otra" and current_state != conversation_flow.STATES["START"]:
                await firebase_manager.reset_user_state(from_number)
                await self.send_message(from_number, conversation_flow.get_welcome_message())
                return
            
            # Validar entrada
            is_valid, processed_value = conversation_flow.validate_input(current_state, text)
            
            if not is_valid:
                # Enviar mensaje de error
                error_message = conversation_flow.get_error_message(current_state)
                await self.send_message(from_number, error_message)
                return
            
            # Actualizar datos del usuario
            if current_state == conversation_flow.STATES["GET_CROP"]:
                user_data["crop"] = processed_value
            elif current_state == conversation_flow.STATES["GET_AREA"]:
                user_data["area"] = processed_value
            elif current_state == conversation_flow.STATES["GET_CHANNEL"]:
                user_data["commercialization"] = processed_value
            elif current_state == conversation_flow.STATES["GET_IRRIGATION"]:
                user_data["irrigation"] = processed_value
            elif current_state == conversation_flow.STATES["GET_LOCATION"]:
                user_data["location"] = processed_value
            
            # Obtener siguiente estado
            next_state = conversation_flow.get_next_state(current_state, text)
            
            # Procesar estado actual
            if next_state == conversation_flow.STATES["SHOW_REPORT"]:
                # Generar y enviar reporte
                report = await conversation_flow.process_show_report(user_data)
                await self.send_message(from_number, report)
                
            elif next_state == conversation_flow.STATES["SHOW_LOAN"]:
                # Mostrar oferta de préstamo
                loan_offer = conversation_flow.process_show_loan(user_data)
                await self.send_message(from_number, loan_offer)
                
            elif next_state == conversation_flow.STATES["DONE"]:
                if current_state == conversation_flow.STATES["CONFIRM_LOAN"] and processed_value:
                    # Enviar mensaje de confirmación
                    success_message = conversation_flow.process_confirm_loan()
                    await self.send_message(from_number, success_message)
                else:
                    # Usuario no quiere préstamo
                    await self.send_message(
                        from_number,
                        "👋 Gracias por usar FinGro. Escribe *otra* para analizar otro cultivo."
                    )
                    
            else:
                # Enviar siguiente mensaje
                next_message = conversation_flow.get_next_message(next_state, user_data)
                await self.send_message(from_number, next_message)
            
            # Actualizar estado en Firebase
            await firebase_manager.update_user_state(
                from_number,
                {
                    "state": next_state,
                    "data": user_data,
                    "last_update": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            await self.send_message(
                from_number,
                "❌ Ha ocurrido un error. Por favor intenta de nuevo más tarde."
            )

    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()

# Instancia global
whatsapp_service = WhatsAppService()
