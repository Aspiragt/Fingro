from dotenv import load_dotenv
import os
from twilio.rest import Client

def send_test_message(to_number):
    # Cargar variables de entorno
    load_dotenv()
    
    # Configurar cliente de Twilio
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
    client = Client(account_sid, auth_token)
    
    try:
        # Enviar mensaje de prueba
        message = client.messages.create(
            from_=f"whatsapp:{twilio_number}",
            body="¡Hola! 🌱 Este es un mensaje de prueba de Fingro.",
            to=f"whatsapp:{to_number}"
        )
        
        print("✅ Mensaje enviado exitosamente")
        print(f"ID del mensaje: {message.sid}")
        return True
    except Exception as e:
        print("❌ Error al enviar mensaje:")
        print(str(e))
        return False

if __name__ == "__main__":
    # Número de WhatsApp del usuario
    YOUR_PHONE_NUMBER = "+50253023697"  # Formato internacional sin espacios
    send_test_message(YOUR_PHONE_NUMBER)
