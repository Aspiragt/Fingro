"""
Constantes y mensajes del sistema
"""
from enum import Enum

class ConversationState(str, Enum):
    """Estados de la conversación"""
    INITIAL = "initial"
    ASKING_AREA = "asking_area"
    ASKING_IRRIGATION = "asking_irrigation"
    ASKING_COMMERCIALIZATION = "asking_commercialization"
    ASKING_LOCATION = "asking_location"
    ASKING_LOAN_INTEREST = "asking_loan_interest"
    COMPLETED = "completed"

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

MESSAGES = {
    'welcome': """
👋 ¡Hola! Soy el asistente de FinGro.

Estoy aquí para ayudarte a obtener financiamiento para tu proyecto agrícola.

Para empezar, dime qué cultivo planeas sembrar 🌱
(Por ejemplo: maíz, frijol, tomate, etc.)
""",

    'ask_area': """
¿Cuántas hectáreas planeas sembrar? 🌾

Por favor, escribe solo el número.
Ejemplo: 2.5
""",

    'ask_irrigation': """
¿Qué sistema de riego usarás? 💧

Opciones:
- Goteo
- Aspersión
- Gravedad
- Temporal (lluvia)
""",

    'ask_commercialization': """
¿Cómo planeas vender tu cosecha? 🏪

Opciones:
- Mercado local (venta directa en mercados o tiendas)
- Intermediario (venta a mayoristas)
- Exportación (venta al extranjero)
- Directo (venta directa a empresas o cooperativas)
""",

    'ask_location': """
¿En qué municipio está tu terreno? 📍

Por favor, escribe el nombre del municipio.
""",

    'ask_loan_interest': """
¿Te gustaría solicitar un préstamo con estas condiciones? 💰

Por favor responde "sí" o "no"
""",

    'loan_yes': """
¡Excelente! 🎉

Un asesor de FinGro se pondrá en contacto contigo pronto para continuar con tu solicitud.

Mientras tanto, puedes ir preparando estos documentos:
- DPI
- Título de propiedad o contrato de arrendamiento
- Recibo de luz o agua reciente
""",

    'loan_no': """
¡Gracias por usar FinGro! 👋

Si cambias de opinión o necesitas más información, escribe "reiniciar" para comenzar de nuevo.
""",

    'unknown': """
❌ No entendí tu respuesta.

Por favor, revisa las opciones disponibles y vuelve a intentar.
""",

    'error': """
😕 Lo siento, hubo un error.

Por favor escribe "reiniciar" para comenzar de nuevo.
""",

    'invalid_area': """
❌ El área debe ser un número válido mayor a 0.

Por favor, escribe solo el número.
Ejemplo: 2.5
"""
}
