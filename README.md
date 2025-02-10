# Fingro - Financiamiento Agrícola Inteligente 🌱

Sistema de scoring crediticio basado en WhatsApp para productores agrícolas en LATAM.

## Características Principales 🚀

- Interacción vía WhatsApp sin necesidad de apps adicionales
- Scoring inteligente basado en huella digital
- Integración con Firebase para almacenamiento seguro
- Motor de ML para evaluación crediticia
- API REST para integración con fintechs y cooperativas

## Configuración Inicial 🛠️

1. Crear archivo `.env` con las credenciales:
```
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_whatsapp_number
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Iniciar el servidor:
```bash
python app.py
```

## Despliegue en Render

1. Crear una cuenta en [Render](https://render.com) si no tienes una

2. Conectar tu repositorio de GitHub a Render:
   - Ve a https://dashboard.render.com/
   - Haz clic en "New +"
   - Selecciona "Web Service"
   - Conecta tu repositorio de GitHub
   - Selecciona el repositorio de Fingro

3. Configurar el servicio:
   - **Name**: `fingro-whatsapp`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

4. Configurar variables de entorno:
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

5. Hacer clic en "Create Web Service"

## Configuración de Webhook

1. Usar la URL de Render como base para el webhook:
   `https://fingro-whatsapp.onrender.com/webhook/whatsapp`

2. En Meta for Developers:
   - Ir a WhatsApp > Configuration
   - Configurar Webhook URL y Verify Token
   - Suscribirse a los eventos de mensajes

## Estructura del Proyecto 📁

- `/app` - Código principal de la aplicación
  - `/models` - Modelos de ML y scoring
  - `/services` - Servicios de WhatsApp y Firebase
  - `/routes` - Endpoints de la API
- `/tests` - Tests unitarios y de integración
- `/docs` - Documentación adicional

## Métricas de Éxito 📊

- 50% tasa de completitud de encuesta en WhatsApp
- Tasa de interés competitiva vs prestamistas informales
- Feedback positivo sobre facilidad de uso
