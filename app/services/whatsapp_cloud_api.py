import os
import requests
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class WhatsAppCloudAPI:
    def __init__(self):
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.api_version = 'v21.0'
        self.api_url = f'https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages'

    def _get_headers(self) -> dict[str, str]:
        """Retorna los headers necesarios para la API de WhatsApp"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def send_text_message(self, to_number: str, message: str) -> dict:
        """Envía un mensaje de texto simple"""
        to_number = to_number.lstrip('+')
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Server response: {e.response.text}")
            raise e

    def send_template_message(
        self, 
        to_number: str, 
        template_name: str, 
        language_code: str = "es",
        components: Optional[List[dict]] = None
    ) -> dict:
        """Envía un mensaje de plantilla con componentes opcionales"""
        to_number = to_number.lstrip('+')
        
        template = {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
        
        if components:
            template["components"] = components
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": template
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending template message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Server response: {e.response.text}")
            raise e

    def send_interactive_message(
        self, 
        to_number: str, 
        interactive_data: dict
    ) -> dict:
        """Envía un mensaje interactivo (botones, listas, etc.)"""
        to_number = to_number.lstrip('+')
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "interactive",
            "interactive": interactive_data
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending interactive message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Server response: {e.response.text}")
            raise e

    def send_location_request(self, to_number: str) -> dict:
        """Envía una solicitud de ubicación"""
        return self.send_text_message(
            to_number,
            "📍 Por favor, comparte tu ubicación para poder darte información más precisa."
        )

    def send_list_message(
        self, 
        to_number: str, 
        header: str,
        body: str,
        footer: str,
        button_text: str,
        sections: List[dict]
    ) -> dict:
        """Envía un mensaje con lista de opciones"""
        interactive_data = {
            "type": "list",
            "header": {
                "type": "text",
                "text": header
            },
            "body": {
                "text": body
            },
            "footer": {
                "text": footer
            },
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
        
        return self.send_interactive_message(to_number, interactive_data)

    def send_button_message(
        self, 
        to_number: str, 
        header: str,
        body: str,
        footer: str,
        buttons: List[dict]
    ) -> dict:
        """Envía un mensaje con botones"""
        interactive_data = {
            "type": "button",
            "header": {
                "type": "text",
                "text": header
            },
            "body": {
                "text": body
            },
            "footer": {
                "text": footer
            },
            "action": {
                "buttons": buttons
            }
        }
        
        return self.send_interactive_message(to_number, interactive_data)

    def mark_message_as_read(self, message_id: str) -> dict:
        """Marca un mensaje como leído"""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error marking message as read: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Server response: {e.response.text}")
            raise e
