"""
Constantes y mensajes del chatbot
"""
from enum import Enum, auto

class ConversationState(str, Enum):
    """Estados de la conversación del chatbot"""
    INITIAL = "INITIAL"
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
    'welcome': """¡Hola! 👋 Soy el asistente de FinGro, una empresa guatemalteca dedicada a apoyar agricultores con financiamiento rápido y justo.

Le ayudamos a obtener el préstamo que necesita para su siembra, sin exceso de papeleo y desde la comodidad de su teléfono 🌱

¿Qué cultivo está sembrando o planea sembrar? Por ejemplo: maíz, frijol, café, etc.""",

    'ask_crop': "🌿 ¿Qué cultivo planeas sembrar?",
    
    'ask_area': """¡Excelente! ¿Qué extensión de terreno cultivará? 
Puede indicarlo en cuerdas, manzanas o hectáreas 🌾""",
    
    'invalid_area': "❌ Ingresa un número válido (ejemplo: 2.5)",
    
    'ask_irrigation': """¿Qué sistema de riego utiliza en su terreno? 💧

1. Temporal (lluvia)
2. Goteo
3. Aspersión
4. Otro""",
    
    'ask_commercialization': """¿Cómo planea comercializar su cosecha? 🚛

1. Mercado local
2. Intermediario
3. Exportación
4. Directo""",
    
    'ask_payment_method': "💵 ¿Forma de pago?\n\n- Efectivo\n- Transferencia\n- Cheque",
    
    'ask_location': "¿En qué municipio está ubicado su terreno? 📍",
    
    'analysis_ready': (
        "✅ ¡Análisis listo!\n\n"
        "📊 FinGro Score: {score}/100\n"
        "💰 Préstamo sugerido: {monto}\n\n"
        "¿Te gustaría aplicar?"
    ),
    
    'analysis': """¡Perfecto! Según los precios actuales del mercado, con su siembra de {cultivo} en {area}:

📈 PROYECCIÓN:
• Ingresos esperados: Q{ingresos}
• Costos estimados: Q{costos}
• Ganancia potencial: Q{ganancia}

¿Le gustaría conocer las opciones de financiamiento disponibles? 💪""",
    
    'credit_offer': """¡Buenas noticias! 🎉 Califica para:

💰 Monto: hasta Q{monto}
📊 Tasa: {tasa}% anual
⏱️ Plazo: {plazo} meses
📅 Cuotas: Q{cuota}/mes

Este préstamo le permite cubrir sus costos de siembra y le da la oportunidad de pagar con su cosecha 🌱

¿Desea iniciar su solicitud? Es rápido y fácil 📝""",
    
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
    
    'error': """¡Disculpe! Tuvimos un pequeño problema técnico 😅 
¿Podría intentar escribir su mensaje nuevamente?""",
    
    'error_restart': "❌ Error. Empecemos de nuevo.\n\n¿Cuál es tu nombre?",
    
    'unknown': "Disculpe, no comprendí bien. ¿Podría reformular su respuesta?"
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
