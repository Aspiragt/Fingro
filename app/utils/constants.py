"""
Constantes y mensajes del chatbot
"""
from enum import Enum, auto

class ConversationState(str, Enum):
    """Estados de la conversación del chatbot"""
    INITIAL = "INITIAL"
    ASKING_CROP = "ASKING_CROP"
    ASKING_AREA = "ASKING_AREA"
    ASKING_IRRIGATION = "ASKING_IRRIGATION"
    ASKING_COMMERCIALIZATION = "ASKING_COMMERCIALIZATION"
    ASKING_LOCATION = "ASKING_LOCATION"
    ANALYSIS = "ANALYSIS"
    COMPLETED = "COMPLETED"

    def __str__(self):
        return self.value

# Mensajes del bot
MESSAGES = {
    'welcome': (
        "👋 ¡Hola! Soy FinGro, tu aliado financiero para el campo.\n\n"
        "🌱 Te ayudaré a conseguir el financiamiento que necesitas para tu cultivo.\n\n"
        "✨ *Beneficios de FinGro:*\n"
        "• Análisis financiero GRATIS\n"
        "• Préstamos desde Q5,000 hasta Q100,000\n"
        "• Tasas preferenciales para agricultores\n"
        "• Respuesta en 24 horas\n\n"
        "🚀 Para empezar, ¿cuál es tu nombre?"
    ),
    
    'ask_crop': "🌿 ¿Qué cultivo planeas sembrar?",
    
    'ask_area': "📏 ¿Cuántas hectáreas planeas cultivar?\n\nPor favor, ingresa solo el número (ejemplo: 2.5)",
    
    'invalid_area': "❌ Por favor, ingresa un número válido para el área (ejemplo: 2.5)",
    
    'ask_irrigation': "💧 ¿Qué sistema de riego utilizarás?\n\nEscribe una de estas opciones:\n- Goteo\n- Aspersión\n- Gravedad\n- Temporal",
    
    'ask_commercialization': "🏪 ¿Cómo planeas comercializar tu cosecha?\n\nEscribe una opción:\n- Mercado local\n- Exportación\n- Intermediario\n- Directo",
    
    'ask_location': "📍 ¿En qué municipio y departamento está ubicada tu parcela?\n\nEjemplo: San Juan Sacatepéquez, Guatemala",
    
    'analysis_ready': "✅ ¡Tu análisis está listo!\n\nUn asesor de FinGro se pondrá en contacto contigo pronto para discutir las opciones de financiamiento disponibles para tu proyecto.",
    
    'error': "❌ Lo siento, ha ocurrido un error. Por favor escribe 'reiniciar' para comenzar de nuevo.",
    
    'error_restart': "❌ Ha ocurrido un error. Vamos a comenzar de nuevo.\n\n¿Cuál es tu nombre?"
}

def format_currency(amount: float) -> str:
    """Formatea cantidades monetarias"""
    return f"Q{amount:,.2f}"

# Variaciones de escritura comunes
CROP_VARIATIONS = {
    "maiz": ["maiz", "maíz", "mais", "elote"],
    "frijol": ["frijol", "frijoles", "frijoles negros", "frijol negro"],
    "papa": ["papa", "papas", "patata", "patatas"],
    "tomate": ["tomate", "tomates", "jitomate"],
    "chile": ["chile", "chiles", "chile pimiento", "pimiento"],
    "cebolla": ["cebolla", "cebollas"],
    "zanahoria": ["zanahoria", "zanahorias"],
    "arveja": ["arveja", "arvejas", "guisante"],
    "ejote": ["ejote", "ejotes", "judía verde"],
    "brócoli": ["brócoli", "brocoli", "brocolí", "broccoli"],
    "lechuga": ["lechuga", "lechugas"],
    "repollo": ["repollo", "repollos", "col"],
    "coliflor": ["coliflor", "coliflores"],
    "remolacha": ["remolacha", "remolachas", "betabel"],
    "pepino": ["pepino", "pepinos"],
    "calabaza": ["calabaza", "calabazas", "ayote"],
    "güisquil": ["güisquil", "guisquil", "chayote"],
    "café": ["café", "cafe", "cafeto"],
    "cardamomo": ["cardamomo", "cardamomo verde"],
    "aguacate": ["aguacate", "aguacates", "palta"],
    "plátano": ["plátano", "platano", "banano", "guineo"],
    "piña": ["piña", "piñas", "ananás"],
    "papaya": ["papaya", "papayas"],
    "mango": ["mango", "mangos"],
    "limón": ["limón", "limon", "limones"],
    "naranja": ["naranja", "naranjas"],
    "mandarina": ["mandarina", "mandarinas"],
    "fresa": ["fresa", "fresas"],
    "mora": ["mora", "moras", "zarzamora"],
    "frambuesa": ["frambuesa", "frambuesas"]
}
