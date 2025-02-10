from dotenv import load_dotenv
import os
from twilio.rest import Client

def test_twilio_connection():
    # Cargar variables de entorno
    load_dotenv()
    
    # Configurar cliente de Twilio
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    
    try:
        # Verificar que podemos acceder a la cuenta
        account = client.api.accounts(account_sid).fetch()
        print("✅ Conexión exitosa con Twilio")
        print(f"Nombre de la cuenta: {account.friendly_name}")
        return True
    except Exception as e:
        print("❌ Error al conectar con Twilio:")
        print(str(e))
        return False

if __name__ == "__main__":
    test_twilio_connection()
