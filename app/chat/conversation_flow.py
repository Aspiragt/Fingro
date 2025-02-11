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
    
    async def handle_message(self, phone: str, message: str) -> Tuple[str, Optional[List[Dict[str, str]]]]:
        """
        Maneja un mensaje entrante y retorna la respuesta
        
        Args:
            phone: Número de teléfono del usuario
            message: Mensaje recibido
            
        Returns:
            Tuple[str, Optional[List[Dict[str, str]]]]: Mensaje de respuesta y archivos adjuntos opcionales
        """
        try:
            # Normalizar mensaje
            message = message.strip().lower()
            
            # Obtener estado actual
            state = await firebase_manager.get_conversation_state(phone)
            if not state:
                state = ConversationState.INITIAL
                await firebase_manager.update_user_state(phone, state)
            
            # Obtener manejador para el estado actual
            handler = self.state_handlers.get(state)
            if not handler:
                logger.error(f"No handler found for state: {state}")
                return MESSAGES['error'], None
            
            # Procesar mensaje según el estado
            return await handler(phone, message)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return MESSAGES['error'], None
    
    async def _handle_initial_state(self, phone: str, message: str) -> Tuple[str, None]:
        """Maneja el estado inicial"""
        await firebase_manager.update_user_state(phone, ConversationState.ASKING_CROP)
        return MESSAGES['ask_crop'], None
    
    async def _handle_crop_state(self, phone: str, message: str) -> Tuple[str, None]:
        """Maneja el estado de pregunta sobre cultivo"""
        # Validar cultivo
        crop = None
        for crop_name, variations in CROP_VARIATIONS.items():
            if message in variations:
                crop = crop_name
                break
        
        if not crop:
            return "No reconozco ese cultivo. Por favor, elige uno de la lista:\n" + \
                   "\n".join([f"- {crop}" for crop in CROP_VARIATIONS.keys()]), None
        
        # Guardar cultivo y actualizar estado
        await firebase_manager.update_user_data(phone, {'crop': crop})
        await firebase_manager.update_user_state(phone, ConversationState.ASKING_AREA)
        return MESSAGES['ask_area'], None
    
    async def _handle_area_state(self, phone: str, message: str) -> Tuple[str, None]:
        """Maneja el estado de pregunta sobre área"""
        try:
            area = float(message.replace(',', '.'))
            if area <= 0:
                return MESSAGES['invalid_area'], None
                
            await firebase_manager.update_user_data(phone, {'area': area})
            await firebase_manager.update_user_state(phone, ConversationState.ASKING_IRRIGATION)
            return MESSAGES['ask_irrigation'], None
            
        except ValueError:
            return MESSAGES['invalid_area'], None
    
    async def _handle_irrigation_state(self, phone: str, message: str) -> Tuple[str, None]:
        """Maneja el estado de pregunta sobre riego"""
        valid_irrigation = ['goteo', 'aspersion', 'aspersión', 'gravedad', 'temporal']
        if message not in valid_irrigation:
            return "Por favor, elige un sistema de riego válido:\n- Goteo\n- Aspersión\n- Gravedad\n- Temporal", None
        
        await firebase_manager.update_user_data(phone, {'irrigation': message})
        await firebase_manager.update_user_state(phone, ConversationState.ASKING_COMMERCIALIZATION)
        return MESSAGES['ask_commercialization'], None
    
    async def _handle_commercialization_state(self, phone: str, message: str) -> Tuple[str, None]:
        """Maneja el estado de pregunta sobre comercialización"""
        valid_commercialization = ['mercado local', 'exportacion', 'exportación', 'intermediario', 'directo']
        if message not in valid_commercialization:
            return "Por favor, elige un método de comercialización válido:\n- Mercado local\n- Exportación\n- Intermediario\n- Directo", None
        
        await firebase_manager.update_user_data(phone, {'commercialization': message})
        await firebase_manager.update_user_state(phone, ConversationState.ASKING_LOCATION)
        return MESSAGES['ask_location'], None
    
    async def _handle_location_state(self, phone: str, message: str) -> Tuple[str, None]:
        """Maneja el estado de pregunta sobre ubicación"""
        await firebase_manager.update_user_data(phone, {'location': message})
        await firebase_manager.update_user_state(phone, ConversationState.ANALYSIS)
        return MESSAGES['analysis_ready'], None
    
    async def _handle_analysis_state(self, phone: str, message: str) -> Tuple[str, Optional[List[Dict[str, str]]]]:
        """Maneja el estado de análisis"""
        try:
            # Obtener datos del usuario
            user_data = await firebase_manager.get_user_data(phone)
            if not user_data:
                return MESSAGES['error'], None
            
            # Obtener precio del cultivo
            crop_price = await maga_api.get_precio_cultivo(user_data['crop'])
            
            # Calcular score y recomendaciones
            score_data = await scoring_service.calculate_score(user_data, crop_price)
            
            # Generar reporte
            report = (
                f"✅ *¡Análisis completado!*\n\n"
                f"📝 *Datos del Proyecto*\n"
                f"• Cultivo: {user_data['crop']}\n"
                f"• Área: {user_data['area']} hectáreas\n"
                f"• Riego: {user_data['irrigation']}\n"
                f"• Comercialización: {user_data['commercialization']}\n"
                f"• Ubicación: {user_data['location']}\n\n"
                f"💰 *Análisis Financiero*\n"
                f"• Inversión necesaria: {format_currency(score_data['costos_estimados'])}\n"
                f"• Ingresos proyectados: {format_currency(score_data['ingreso_estimado'])}\n"
                f"• Ganancia estimada: {format_currency(score_data['ganancia_estimada'])}\n"
                f"• FinGro Score: {score_data['fingro_score']}%\n\n"
                f"🎉 *¡Buenas noticias!*\n"
                f"Calificas para un préstamo de hasta {format_currency(score_data['prestamo_recomendado'])}.\n\n"
                f"🏦 ¿Listo para solicitar tu préstamo? Escribe 'solicitar' para comenzar el proceso."
            )
            
            await firebase_manager.update_user_state(phone, ConversationState.COMPLETED)
            return report, None
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return MESSAGES['error'], None
    
    async def _handle_completed_state(self, phone: str, message: str) -> Tuple[str, None]:
        """Maneja el estado completado"""
        if message == 'solicitar':
            # TODO: Implementar lógica para iniciar solicitud de préstamo
            return "Pronto un asesor se pondrá en contacto contigo para continuar con tu solicitud. ¡Gracias por usar FinGro! 🙌", None
        return "Escribe 'solicitar' para comenzar el proceso de préstamo o 'reiniciar' para comenzar de nuevo.", None

def format_currency(amount: float) -> str:
    """Formatea cantidades monetarias"""
    return f"Q{amount:,.2f}"

# Instancia global
conversation_manager = ConversationManager()
