from enum import Enum, auto

class ConversationState(str, Enum):
    """Estados de la conversación del chatbot"""
    INICIO = "INICIO"
    CULTIVO = "CULTIVO"
    HECTAREAS = "HECTAREAS"
    RIEGO = "RIEGO"
    COMERCIALIZACION = "COMERCIALIZACION"
    UBICACION = "UBICACION"
    FINALIZADO = "FINALIZADO"

    def __str__(self):
        return self.value

# Mensajes del bot
MESSAGES = {
    ConversationState.INICIO: (
        "👋 ¡Hola! Soy FinGro, tu aliado financiero para el campo.\n\n"
        "🌱 Te ayudaré a conseguir el financiamiento que necesitas para tu cultivo.\n\n"
        "✨ *Beneficios de FinGro:*\n"
        "• Análisis financiero GRATIS\n"
        "• Préstamos desde Q5,000 hasta Q100,000\n"
        "• Tasas preferenciales para agricultores\n"
        "• Respuesta en 24 horas\n\n"
        "🚀 *¿Empezamos?*\n"
        "¿Qué cultivo planeas sembrar?"
    ),
    
    ConversationState.CULTIVO: "🌿 ¿Cuántas hectáreas planeas cultivar?\n\nPor favor, ingresa solo el número (ejemplo: 2.5)",
    
    ConversationState.HECTAREAS: "💧 ¿Qué sistema de riego utilizarás?\n\nEscribe una de estas opciones:\n- Goteo\n- Aspersión\n- Gravedad\n- Temporal",
    
    ConversationState.RIEGO: "🏪 ¿Cómo planeas comercializar tu cosecha?\n\nEscribe una opción:\n- Mercado local\n- Exportación\n- Intermediario\n- Directo",
    
    ConversationState.COMERCIALIZACION: "📍 ¿En qué municipio y departamento está ubicada tu parcela?\n\nEjemplo: San Juan Sacatepéquez, Guatemala",
    
    ConversationState.UBICACION: "⌛ Analizando tu proyecto...",
    
    ConversationState.FINALIZADO: lambda data: (
        f"✅ *¡Análisis completado!*\n\n"
        f"📝 *Datos del Proyecto*\n"
        f"• Cultivo: {data['cultivo']}\n"
        f"• Área: {data['hectareas']} hectáreas\n"
        f"• Riego: {data['riego']}\n"
        f"• Comercialización: {data['comercializacion']}\n"
        f"• Ubicación: {data['ubicacion']}\n\n"
        f"💰 *Análisis Financiero*\n"
        f"• Inversión necesaria: {format_currency(data['score_data']['costos_estimados'])}\n"
        f"• Ingresos proyectados: {format_currency(data['score_data']['ingreso_estimado'])}\n"
        f"• Ganancia estimada: {format_currency(data['score_data']['ganancia_estimada'])}\n"
        f"• FinGro Score: {data['score_data']['fingro_score']}%\n\n"
        f"🎉 *¡Buenas noticias!*\n"
        f"Calificas para un préstamo de hasta {format_currency(data['score_data']['prestamo_recomendado'])}.\n\n"
        f"🏦 ¿Listo para solicitar tu préstamo? Escribe 'solicitar' para comenzar el proceso."
    )
}

def format_currency(amount: float) -> str:
    """Formatea cantidades monetarias"""
    return f"Q{amount:,.2f}"

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

# Respuestas comunes para cada estado
VALID_RESPONSES = {
    ConversationState.RIEGO: ['goteo', 'aspersión', 'gravedad', 'temporal'],
    ConversationState.COMERCIALIZACION: ['mercado local', 'exportación', 'intermediario', 'directo']
}

# Comandos especiales
SPECIAL_COMMANDS = {
    'reiniciar': 'Reinicia la conversación',
    'ayuda': 'Muestra el menú de ayuda',
    'solicitar': 'Inicia el proceso de solicitud de préstamo'
}
