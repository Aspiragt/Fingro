"""
Módulo para manejar el flujo de conversación con el usuario
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

class ConversationState(Enum):
    """Estados posibles de la conversación"""
    INIT = "init"
    ASK_CROP = "ask_crop"
    ASK_AREA = "ask_area"
    ASK_MARKET = "ask_market"
    ASK_IRRIGATION = "ask_irrigation"
    ASK_LOCATION = "ask_location"
    SHOW_ANALYSIS = "show_analysis"
    WAITING_CONFIRMATION = "waiting_confirmation"

class MarketType(Enum):
    """Tipos de comercialización"""
    LOCAL = "Mercado local"
    EXPORT = "Exportación"
    INTERMEDIARY = "Intermediario"
    OTHER = "Otro"

class IrrigationType(Enum):
    """Tipos de riego"""
    DRIP = "Goteo"
    SPRINKLER = "Aspersión"
    GRAVITY = "Gravedad"
    NONE = "No tengo riego"

@dataclass
class ProjectData:
    """Datos del proyecto agrícola"""
    crop_name: Optional[str] = None
    area_ha: Optional[float] = None
    market_type: Optional[MarketType] = None
    irrigation_type: Optional[IrrigationType] = None
    location: Optional[str] = None
    created_at: datetime = datetime.now()

class ConversationManager:
    """Maneja el flujo de conversación"""
    
    def __init__(self):
        self.state = ConversationState.INIT
        self.project_data = ProjectData()
    
    def get_welcome_message(self) -> str:
        """Mensaje de bienvenida"""
        return (
            "¡Hola! 👋 Soy Figo de FinGro 🌱\n"
            "Analizaré tu proyecto agrícola para un posible financiamiento.\n"
            "¿Qué cultivo sembrarás? 🌱"
        )
    
    def get_next_question(self) -> str:
        """Obtiene la siguiente pregunta según el estado"""
        if self.state == ConversationState.INIT:
            self.state = ConversationState.ASK_CROP
            return self.get_welcome_message()
            
        elif self.state == ConversationState.ASK_CROP:
            self.state = ConversationState.ASK_AREA
            return "¿Cuántas hectáreas? 📏"
            
        elif self.state == ConversationState.ASK_AREA:
            self.state = ConversationState.ASK_MARKET
            return (
                "¿Dónde venderás tu cosecha? 🚛\n"
                "1. 🏪 Mercado local\n"
                "2. 🌎 Exportación\n"
                "3. 🤝 Intermediario\n"
                "4. 📦 Otro"
            )
            
        elif self.state == ConversationState.ASK_MARKET:
            self.state = ConversationState.ASK_IRRIGATION
            return (
                "¿Sistema de riego? 💧\n"
                "1. 💧 Goteo\n"
                "2. 🌧️ Aspersión\n"
                "3. ⛰️ Gravedad\n"
                "4. ❌ No tengo"
            )
            
        elif self.state == ConversationState.ASK_IRRIGATION:
            self.state = ConversationState.ASK_LOCATION
            return "¿Municipio y departamento? 📍"
            
        elif self.state == ConversationState.ASK_LOCATION:
            self.state = ConversationState.SHOW_ANALYSIS
            return "Analizando... ⚡️"
            
        return ""
    
    def process_answer(self, answer: str) -> Optional[str]:
        """Procesa la respuesta del usuario"""
        if self.state == ConversationState.ASK_CROP:
            self.project_data.crop_name = answer.lower()
            
        elif self.state == ConversationState.ASK_AREA:
            try:
                self.project_data.area_ha = float(answer)
                if self.project_data.area_ha <= 0:
                    return "El área debe ser mayor a 0"
            except ValueError:
                return "Ingresa un número válido (ejemplo: 1.5)"
                
        elif self.state == ConversationState.ASK_MARKET:
            market_map = {
                "1": MarketType.LOCAL,
                "2": MarketType.EXPORT,
                "3": MarketType.INTERMEDIARY,
                "4": MarketType.OTHER
            }
            if answer not in market_map:
                return "Elige un número del 1 al 4"
            self.project_data.market_type = market_map[answer]
            
        elif self.state == ConversationState.ASK_IRRIGATION:
            irrigation_map = {
                "1": IrrigationType.DRIP,
                "2": IrrigationType.SPRINKLER,
                "3": IrrigationType.GRAVITY,
                "4": IrrigationType.NONE
            }
            if answer not in irrigation_map:
                return "Elige un número del 1 al 4"
            self.project_data.irrigation_type = irrigation_map[answer]
            
        elif self.state == ConversationState.ASK_LOCATION:
            self.project_data.location = answer
            
        return None  # Sin error
    
    def is_ready_for_analysis(self) -> bool:
        """Verifica si tenemos todos los datos necesarios"""
        return all([
            self.project_data.crop_name,
            self.project_data.area_ha,
            self.project_data.market_type,
            self.project_data.irrigation_type,
            self.project_data.location
        ])

    async def handle_special_command(self, phone_number: str, command: str) -> str:
        """
        Maneja comandos especiales como 'reiniciar' o 'ayuda'
        """
        try:
            if command == 'reiniciar':
                # Reiniciar completamente la conversación
                await db.reset_conversation(phone_number)
                logger.info(f"Conversación reiniciada para {phone_number}")
                return "🔄 Conversación reiniciada.\n\n" + MESSAGES[ConversationState.INIT]
                
            elif command == 'ayuda':
                return ("🤖 *Comandos disponibles:*\n" +
                        "\n".join([f"• {cmd}: {desc}" for cmd, desc in SPECIAL_COMMANDS.items()]))
                        
            elif command == 'solicitar':
                return ("🏦 Para solicitar tu préstamo, necesitaremos:\n\n"
                        "📄 1. DPI\n"
                        "📝 2. Comprobante de domicilio\n"
                        "🏡 3. Título de propiedad o contrato de arrendamiento\n\n"
                        "Un asesor se pondrá en contacto contigo pronto. 👋")
                        
            return "❓ Comando no reconocido. Escribe 'ayuda' para ver los comandos disponibles."
            
        except Exception as e:
            logger.error(f"Error en handle_special_command: {str(e)}")
            return "❌ Lo siento, ocurrió un error. Por favor, intenta nuevamente."
