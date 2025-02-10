import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class WhatsAppCloudAPI:
    def __init__(self):
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.api_version = 'v21.0'
        self.api_url = f'https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages'
        
    def send_template_message(self, to_number: str, template_name: str, language_code: str = "es") -> Dict:
        """
        Envía un mensaje usando una plantilla predefinida
        """
        # Asegurar que el número tenga el formato correcto (sin + y solo dígitos)
        to_number = to_number.lstrip('+')
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error enviando mensaje: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Respuesta del servidor: {e.response.text}")
            raise e
    
    def send_text_message(self, to_number: str, message: str) -> Dict:
        """
        Envía un mensaje de texto simple
        """
        # Asegurar que el número tenga el formato correcto (sin + y solo dígitos)
        to_number = to_number.lstrip('+')
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
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
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error enviando mensaje: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Respuesta del servidor: {e.response.text}")
            raise e
