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
    ASKING_PAYMENT_METHOD = "ASKING_PAYMENT_METHOD"
    ASKING_LOCATION = "ASKING_LOCATION"
    ANALYSIS = "ANALYSIS"
    ASKING_LOAN_INTEREST = "ASKING_LOAN_INTEREST"
    COMPLETED = "COMPLETED"

    def __str__(self):
        return self.value

# Mensajes del bot
MESSAGES = {
    'welcome': (
        "👋 ¡Hola! Soy FinGro\n\n"
        "🌱 Préstamos para el campo desde Q5,000 hasta Q100,000\n"
        "⚡️ Respuesta en 24 horas\n\n"
        "¿Cuál es tu nombre?"
    ),
    
    'ask_crop': "🌿 ¿Qué cultivo planeas sembrar?",
    
    'ask_area': "📏 ¿Cuántas hectáreas? (ejemplo: 2.5)",
    
    'invalid_area': "❌ Ingresa un número válido (ejemplo: 2.5)",
    
    'ask_irrigation': "💧 ¿Sistema de riego?\n\n- Goteo\n- Aspersión\n- Gravedad\n- Temporal",
    
    'ask_commercialization': "🏪 ¿Cómo venderás?\n\n- Mercado local\n- Exportación\n- Intermediario\n- Directo",
    
    'ask_payment_method': "💵 ¿Forma de pago?\n\n- Efectivo\n- Transferencia\n- Cheque",
    
    'ask_location': "📍 ¿Municipio y departamento?\n\nEjemplo: San Juan Sacatepéquez, Guatemala",
    
    'analysis_ready': (
        "✅ ¡Análisis listo!\n\n"
        "📊 FinGro Score: {score}/100\n"
        "💰 Préstamo sugerido: {monto}\n\n"
        "¿Te gustaría aplicar?"
    ),
    
    'ask_loan_interest': "🤔 ¿Aplicar para un préstamo?\n\nResponde 'si' o 'no'",
    
    'loan_yes': (
        "🎉 ¡Excelente!\n\n"
        "Documentos necesarios:\n"
        "• DPI\n"
        "• Recibo de servicios\n"
        "• Estado de cuenta\n\n"
        "¿Cuándo quieres empezar?"
    ),
    
    'loan_no': "👋 ¡Gracias! Escribe 'reiniciar' cuando quieras intentar de nuevo",
    
    'error': "❌ Error. Escribe 'reiniciar' para comenzar de nuevo",
    
    'error_restart': "❌ Error. Empecemos de nuevo.\n\n¿Cuál es tu nombre?"
}

def format_currency(amount: float) -> str:
    """Formatea cantidades monetarias"""
    return f"Q{amount:,.2f}"

# Variaciones de escritura comunes
CROP_VARIATIONS = {
    'maiz': ['maiz', 'maíz', 'mais', 'elote'],
    'frijol': ['frijol', 'frijoles', 'frijoles negros', 'frijol negro'],
    'papa': ['papa', 'papas', 'patata', 'patatas'],
    'tomate': ['tomate', 'tomates', 'jitomate'],
    'chile': ['chile', 'chiles', 'pimiento', 'pimientos'],
    'cebolla': ['cebolla', 'cebollas'],
    'zanahoria': ['zanahoria', 'zanahorias'],
    'aguacate': ['aguacate', 'aguacates', 'palta'],
    'platano': ['platano', 'plátano', 'platanos', 'plátanos', 'banano'],
    'cafe': ['cafe', 'café'],
    'arroz': ['arroz'],
    'brocoli': ['brocoli', 'brócoli', 'brocolis'],
    'lechuga': ['lechuga', 'lechugas'],
    'repollo': ['repollo', 'repollos', 'col'],
    'arveja': ['arveja', 'arvejas', 'guisante', 'guisantes']
}
