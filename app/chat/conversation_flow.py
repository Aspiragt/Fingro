"""
Módulo para manejar el flujo de conversación
"""
import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from app.database.firebase import firebase_manager
from app.external_apis.maga import maga_api
from app.analysis.scoring import scoring_service
from app.utils.constants import ConversationState, MESSAGES, CROP_VARIATIONS

logger = logging.getLogger(__name__)

class ConversationManager:
    """Maneja el flujo de conversación con el usuario"""
    
    def __init__(self):
        """Inicializa el manejador de conversación"""
        self.state_handlers = {
            ConversationState.INITIAL: self._handle_initial_state,
            ConversationState.ASKING_CROP: self._handle_crop_state,
            ConversationState.ASKING_AREA: self._handle_area_state,
            ConversationState.ASKING_IRRIGATION: self._handle_irrigation_state,
            ConversationState.ASKING_COMMERCIALIZATION: self._handle_commercialization_state,
            ConversationState.ASKING_LOCATION: self._handle_location_state,
            ConversationState.ANALYSIS: self._handle_analysis_state,
            ConversationState.COMPLETED: self._handle_completed_state
        }
    
    async def handle_message(self, phone: str, message: str) -> str:
        """
        Maneja un mensaje entrante y retorna la respuesta
        
        Args:
            phone: Número de teléfono del usuario
            message: Mensaje recibido
            
        Returns:
            str: Mensaje de respuesta
        """
        try:
            # Normalizar mensaje
            message = message.strip().lower()
            
            # Manejar comando de reinicio
            if message == "reiniciar":
                await firebase_manager.reset_user_state(phone)
                return MESSAGES['welcome']
            
            # Obtener estado actual
            conversation_data = firebase_manager.get_conversation_state(phone)
            current_state = conversation_data.get('state', ConversationState.INITIAL.value)
            user_data = conversation_data.get('data', {})
            
            # Procesar mensaje según estado
            if current_state == ConversationState.INITIAL.value:
                user_data['name'] = message.title()  # Capitalizar nombre
                new_state = ConversationState.ASKING_CROP.value
                response = MESSAGES['ask_crop']
                
            elif current_state == ConversationState.ASKING_CROP.value:
                user_data['crop'] = message
                # Obtener precio del cultivo
                try:
                    precio = await maga_api.get_precio_cultivo(message)
                    user_data['precio_info'] = precio
                    logger.info(f"Precio encontrado para {message}: Q{precio}/quintal")
                except Exception as e:
                    logger.error(f"Error obteniendo precios: {str(e)}")
                    # Usar precio por defecto si no se encuentra
                    user_data['precio_info'] = maga_api.default_prices.get(message, 200)
                
                new_state = ConversationState.ASKING_AREA.value
                response = MESSAGES['ask_area']
                
            elif current_state == ConversationState.ASKING_AREA.value:
                try:
                    area = float(message.replace('ha', '').strip())
                    if area <= 0:
                        return MESSAGES['invalid_area']
                    user_data['area'] = area
                    new_state = ConversationState.ASKING_COMMERCIALIZATION.value
                    response = MESSAGES['ask_commercialization']
                except ValueError:
                    return MESSAGES['invalid_area']
                
            elif current_state == ConversationState.ASKING_COMMERCIALIZATION.value:
                valid_options = ['mercado local', 'exportación', 'intermediario', 'directo']
                if message not in valid_options:
                    return (
                        "❌ Por favor, selecciona una opción válida:\n"
                        "- Mercado local\n"
                        "- Exportación\n"
                        "- Intermediario\n"
                        "- Directo"
                    )
                user_data['commercialization'] = message
                new_state = ConversationState.ASKING_IRRIGATION.value
                response = MESSAGES['ask_irrigation']
                
            elif current_state == ConversationState.ASKING_IRRIGATION.value:
                valid_options = ['goteo', 'aspersión', 'gravedad', 'temporal']
                if message not in valid_options:
                    return (
                        "❌ Por favor, selecciona una opción válida:\n"
                        "- Goteo\n"
                        "- Aspersión\n"
                        "- Gravedad\n"
                        "- Temporal"
                    )
                user_data['irrigation'] = message
                new_state = ConversationState.ASKING_LOCATION.value
                response = MESSAGES['ask_location']
                
            elif current_state == ConversationState.ASKING_LOCATION.value:
                user_data['location'] = message
                new_state = ConversationState.ANALYSIS.value
                
                # Generar análisis
                analysis = scoring_service.generate_analysis(user_data)
                firebase_manager.store_analysis(phone, analysis)
                
                # Preparar mensaje de respuesta con el análisis
                fingro_score = analysis.get('fingro_score', 0)
                monto_sugerido = analysis.get('monto_sugerido', 0)
                
                response = (
                    f"✅ ¡{user_data['name']}, tu análisis está listo!\n\n"
                    f"📊 Tu Fingro Score es: {fingro_score}/100\n"
                    f"💰 Monto sugerido: Q{format_currency(monto_sugerido)}\n\n"
                    "👨‍💼 Un asesor de FinGro se pondrá en contacto contigo pronto "
                    "para discutir las opciones de financiamiento disponibles para tu proyecto."
                )
                
            elif current_state == ConversationState.ANALYSIS.value:
                new_state = ConversationState.COMPLETED.value
                response = (
                    "🎉 ¡Gracias por usar FinGro!\n\n"
                    "Si deseas realizar un nuevo análisis, escribe 'reiniciar'."
                )
                
            else:
                await firebase_manager.reset_user_state(phone)
                return MESSAGES['error_restart']
            
            # Actualizar estado
            await firebase_manager.update_user_state(phone, {
                'state': new_state,
                'data': user_data
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error en handle_message: {str(e)}")
            return MESSAGES['error']

def format_currency(amount: float) -> str:
    """Formatea cantidades monetarias"""
    return f"{amount:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".")

# Instancia global
conversation_manager = ConversationManager()
