# Fingro WhatsApp Bot 🌱

Bot de WhatsApp para Fingro, diseñado para ayudar a agricultores a obtener financiamiento de manera rápida y sencilla.

## 🚀 Características

- Integración con WhatsApp Cloud API
- Base de datos en tiempo real con Firebase
- Sistema de puntuación (Fingro Score) para evaluación crediticia
- Manejo de ubicaciones y datos geográficos
- Caché inteligente para respuestas rápidas
- Manejo robusto de errores y excepciones

## 📁 Estructura del Proyecto

```
fingro/
├── app/
│   ├── database/        # Conexión con Firebase
│   ├── models/          # Modelos de datos
│   ├── routes/          # Rutas de la API
│   ├── schemas/         # Esquemas Pydantic
│   ├── services/        # Lógica de negocio
│   ├── utils/           # Utilidades y helpers
│   └── main.py         # Punto de entrada de la aplicación
├── tests/              # Tests unitarios y de integración
├── .env               # Variables de entorno (no versionado)
├── .env.example       # Ejemplo de variables de entorno
├── requirements.txt   # Dependencias del proyecto
└── README.md         # Este archivo
```

## 🛠️ Requisitos

- Python 3.9+
- Cuenta de WhatsApp Business API
- Proyecto de Firebase
- Variables de entorno configuradas

## ⚙️ Configuración

1. Clonar el repositorio:
```bash
git clone https://github.com/fingro/whatsapp-bot.git
cd whatsapp-bot
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

## 🚀 Ejecución

1. Iniciar el servidor:
```bash
uvicorn app.main:app --reload
```

2. Acceder a la documentación de la API:
```
http://localhost:8000/docs
```

## 🔑 Variables de Entorno

```env
# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_ACCESS_TOKEN=tu_access_token

# Firebase
FIREBASE_PROJECT_ID=tu_project_id
FIREBASE_PRIVATE_KEY_ID=tu_private_key_id
FIREBASE_PRIVATE_KEY=tu_private_key
FIREBASE_CLIENT_EMAIL=tu_client_email
FIREBASE_CLIENT_ID=tu_client_id
FIREBASE_CLIENT_X509_CERT_URL=tu_cert_url

# App
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
```

## 📝 API Endpoints

### Webhook
- `GET /api/v1/webhook`: Verificación del webhook de WhatsApp
- `POST /api/v1/webhook`: Recepción de mensajes de WhatsApp

### Health Check
- `GET /api/v1/health`: Estado del servicio y conexiones

## 🧪 Tests

Ejecutar tests:
```bash
pytest
```

## 📦 Despliegue

El proyecto está configurado para despliegue en:
- Render
- Heroku
- Google Cloud Run

Ver `render.yaml` y `Dockerfile` para más detalles.

## 🤝 Contribuir

1. Fork el repositorio
2. Crear una rama (`git checkout -b feature/amazing_feature`)
3. Commit los cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing_feature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.
