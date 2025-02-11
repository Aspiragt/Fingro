# Estados de conversación
CONVERSATION_STATES = {
    "START": "start",
    "WAITING_LOCATION": "waiting_location",
    "ASKING_CROP": "asking_crop",
    "ASKING_AREA": "asking_area",
    "ASKING_IRRIGATION": "asking_irrigation",
    "ASKING_COSTS": "asking_costs",
    "ASKING_SALES": "asking_sales",
    "SHOWING_RESULTS": "showing_results"
}

# Mensajes del bot
MESSAGES = {
    "welcome": """¡Hola! 👋 Soy el asistente de Fingro.
Te ayudaré a conseguir financiamiento para tu cultivo.
Por ejemplo, {name} de {region} recibió {amount} para su cultivo de {crop}.""",

    "location_request": """Para empezar, necesito saber dónde estás.
Por favor, comparte tu ubicación usando el botón de abajo 📍""",

    "crop_request": """¡Gracias! Ahora cuéntame, ¿qué cultivas?
Puedes seleccionar de la lista o escribir tu cultivo.""",

    "area_request": """¿Cuánta área tienes cultivada?
Por ejemplo: 2 hectáreas, 5 manzanas, etc.""",

    "irrigation_request": """¿Qué sistema de riego utilizas?
- Goteo 💧
- Aspersión 🚿
- Lluvia 🌧️""",

    "costs_request": """¿Cuánto inviertes en tu cultivo {crop}?
Incluye costos de:
- Semillas 🌱
- Fertilizantes 🧪
- Mano de obra 👨‍🌾
- Riego 💧""",

    "sales_request": """¿Cómo vendes tu cosecha?
- Mercado local 🏪
- Exportador 🚢
- Intermediario 🤝""",

    "error": """Lo siento, ha ocurrido un error.
Por favor, intenta nuevamente en unos momentos.""",

    "success": """¡Excelente! Basado en tu información:
- Cultivo: {crop}
- Área: {area}
- Score Fingro: {score}
- Financiamiento disponible: Q{amount}

¿Te gustaría conocer las opciones disponibles?"""
}

# Variaciones de escritura comunes
CROP_VARIATIONS = {
    "maiz": ["maiz", "maíz", "mais", "elote"],
    "frijol": ["frijol", "frijoles", "frijoles negros", "frijol negro"],
    "cafe": ["cafe", "café", "cafetal", "cafetos"],
    "tomate": ["tomate", "tomates", "jitomate"],
    "chile": ["chile", "chiles", "pimiento", "pimientos"],
    "papa": ["papa", "papas", "patata", "patatas"]
}

# Unidades de área comunes
AREA_UNITS = {
    "hectarea": ["hectarea", "hectárea", "hectareas", "hectáreas", "ha"],
    "manzana": ["manzana", "manzanas", "mz"],
    "cuerda": ["cuerda", "cuerdas", "cd"]
}

# Factores de conversión a hectáreas
AREA_CONVERSION = {
    "hectarea": 1.0,
    "manzana": 0.7,
    "cuerda": 0.0441
}

# Configuración de puntajes
SCORE_CONFIG = {
    "base_score": 500,
    "irrigation_bonus": {
        "goteo": 100,
        "aspersion": 80,
        "lluvia": 0
    },
    "sales_bonus": {
        "exportador": 100,
        "mercado_local": 50,
        "intermediario": 25
    },
    "area_bonus": {
        "threshold": 5,
        "points": 50
    },
    "response_time_bonus": {
        "threshold": 60,  # segundos
        "points": 50
    }
}
