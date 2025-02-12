"""
Módulo para manejar el flujo de conversación con usuarios
"""
from typing import Dict, Any, Optional
import logging
from app.models.financial_model import financial_model
from app.views.financial_report import report_generator
from app.external_apis.maga import CanalComercializacion
from app.database.firebase import firebase_manager

logger = logging.getLogger(__name__)

class ConversationFlow:
    """Maneja el flujo de conversación con usuarios"""
    
    def __init__(self):
        """Inicializa el manejador de conversación"""
        
        # Estados de la conversación
        self.STATES = {
            'START': 'start',
            'GET_CROP': 'get_crop',
            'GET_AREA': 'get_area',
            'GET_CHANNEL': 'get_channel',
            'GET_IRRIGATION': 'get_irrigation',
            'GET_LOCATION': 'get_location',
            'SHOW_REPORT': 'show_report',
            'ASK_LOAN': 'ask_loan',
            'SHOW_LOAN': 'show_loan',
            'CONFIRM_LOAN': 'confirm_loan',
            'DONE': 'done'
        }
        
        # Opciones válidas
        self.valid_crops = [
            'maiz', 'frijol', 'papa', 'tomate', 'cafe', 'chile',
            'cebolla', 'repollo', 'arveja', 'aguacate', 'platano',
            'limon', 'zanahoria', 'brocoli'
        ]
        
        self.valid_channels = [
            CanalComercializacion.MAYORISTA,
            CanalComercializacion.COOPERATIVA,
            CanalComercializacion.EXPORTACION,
            CanalComercializacion.MERCADO_LOCAL
        ]
        
        self.valid_irrigation = [
            'gravedad', 'aspersion', 'goteo', 'ninguno'
        ]
    
    def get_welcome_message(self) -> str:
        """Retorna mensaje de bienvenida"""
        return (
            "👋 ¡Hola! Soy FinGro, tu asistente financiero agrícola.\n\n"
            "Te ayudaré a analizar la rentabilidad de tu proyecto y "
            "obtener financiamiento. 🌱💰\n\n"
            "Para empezar, *¿qué cultivo planeas sembrar?* 🌾"
        )
    
    def get_next_message(self, current_state: str, user_data: Dict[str, Any]) -> str:
        """
        Obtiene el siguiente mensaje según el estado actual
        
        Args:
            current_state: Estado actual de la conversación
            user_data: Datos del usuario
            
        Returns:
            str: Mensaje para el usuario
        """
        if current_state == self.STATES['GET_AREA']:
            return "¿Cuántas hectáreas planeas sembrar? 🌱"
            
        elif current_state == self.STATES['GET_CHANNEL']:
            channels = [
                "1. Mayorista",
                "2. Cooperativa",
                "3. Exportación",
                "4. Mercado Local"
            ]
            return (
                "¿Cómo planeas comercializar tu producto? 🏪\n\n" +
                "\n".join(channels) +
                "\n\nResponde con el número de tu elección"
            )
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            irrigation = [
                "1. Gravedad",
                "2. Aspersión",
                "3. Goteo",
                "4. Ninguno"
            ]
            return (
                "¿Qué sistema de riego utilizarás? 💧\n\n" +
                "\n".join(irrigation) +
                "\n\nResponde con el número de tu elección"
            )
            
        elif current_state == self.STATES['GET_LOCATION']:
            return "¿En qué departamento está ubicado el terreno? 📍"
            
        return "❌ Estado no válido"
    
    def validate_input(self, current_state: str, user_input: str) -> tuple:
        """
        Valida la entrada del usuario
        
        Args:
            current_state: Estado actual
            user_input: Entrada del usuario
            
        Returns:
            tuple: (es_valido, valor_procesado)
        """
        # Normalizar entrada
        user_input = user_input.lower().strip()
        
        if current_state == self.STATES['GET_CROP']:
            if user_input in self.valid_crops:
                return True, user_input
            return False, None
            
        elif current_state == self.STATES['GET_AREA']:
            try:
                area = float(user_input.replace(',', '.'))
                if 0.1 <= area <= 100:
                    return True, area
            except:
                pass
            return False, None
            
        elif current_state == self.STATES['GET_CHANNEL']:
            try:
                option = int(user_input)
                if 1 <= option <= len(self.valid_channels):
                    return True, self.valid_channels[option - 1]
            except:
                pass
            return False, None
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            try:
                option = int(user_input)
                if 1 <= option <= len(self.valid_irrigation):
                    return True, self.valid_irrigation[option - 1]
            except:
                pass
            return False, None
            
        elif current_state == self.STATES['GET_LOCATION']:
            if len(user_input) > 0:
                return True, user_input
            return False, None
            
        elif current_state in [self.STATES['ASK_LOAN'], self.STATES['CONFIRM_LOAN']]:
            if user_input in ['si', 'no']:
                return True, user_input == 'si'
            return False, None
            
        return False, None
    
    def get_error_message(self, current_state: str) -> str:
        """
        Obtiene mensaje de error según el estado
        
        Args:
            current_state: Estado actual
            
        Returns:
            str: Mensaje de error
        """
        if current_state == self.STATES['GET_CROP']:
            return (
                "❌ Por favor ingresa un cultivo válido\n\n"
                "Algunos ejemplos: maíz, frijol, papa, tomate"
            )
            
        elif current_state == self.STATES['GET_AREA']:
            return (
                "❌ Por favor ingresa un área válida entre 0.1 y 100 hectáreas\n\n"
                "Ejemplo: 2.5"
            )
            
        elif current_state == self.STATES['GET_CHANNEL']:
            return "❌ Por favor selecciona una opción válida (1-4)"
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            return "❌ Por favor selecciona una opción válida (1-4)"
            
        elif current_state == self.STATES['GET_LOCATION']:
            return "❌ Por favor ingresa una ubicación válida"
            
        elif current_state in [self.STATES['ASK_LOAN'], self.STATES['CONFIRM_LOAN']]:
            return "❌ Por favor responde SI o NO"
            
        return "❌ Error desconocido"
    
    def get_next_state(self, current_state: str, user_input: str = None) -> str:
        """
        Obtiene el siguiente estado de la conversación
        
        Args:
            current_state: Estado actual
            user_input: Entrada del usuario opcional
            
        Returns:
            str: Siguiente estado
        """
        if current_state == self.STATES['START']:
            return self.STATES['GET_CROP']
            
        elif current_state == self.STATES['GET_CROP']:
            if user_input and user_input.lower() == 'otra':
                return self.STATES['GET_CROP']
            return self.STATES['GET_AREA']
            
        elif current_state == self.STATES['GET_AREA']:
            return self.STATES['GET_CHANNEL']
            
        elif current_state == self.STATES['GET_CHANNEL']:
            return self.STATES['GET_IRRIGATION']
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            return self.STATES['GET_LOCATION']
            
        elif current_state == self.STATES['GET_LOCATION']:
            return self.STATES['SHOW_REPORT']
            
        elif current_state == self.STATES['SHOW_REPORT']:
            return self.STATES['ASK_LOAN']
            
        elif current_state == self.STATES['ASK_LOAN']:
            if user_input and user_input.lower() == 'si':
                return self.STATES['SHOW_LOAN']
            return self.STATES['DONE']
            
        elif current_state == self.STATES['SHOW_LOAN']:
            return self.STATES['CONFIRM_LOAN']
            
        elif current_state == self.STATES['CONFIRM_LOAN']:
            return self.STATES['DONE']
            
        return self.STATES['START']
    
    async def process_show_report(self, user_data: Dict[str, Any]) -> str:
        """
        Procesa y muestra el reporte financiero
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            str: Reporte formateado
        """
        try:
            # Analizar proyecto
            score_data = await financial_model.analyze_project(user_data)
            
            if not score_data:
                return (
                    "❌ Error generando análisis financiero\n\n"
                    "Por favor intenta de nuevo más tarde."
                )
            
            # Guardar datos del análisis para usarlos después
            user_data['score_data'] = score_data
            
            # Generar reporte simple
            return report_generator.generate_report(user_data, score_data)
            
        except Exception as e:
            logger.error(f"Error procesando reporte: {str(e)}")
            return (
                "❌ Error generando reporte\n\n"
                "Por favor intenta de nuevo más tarde."
            )
    
    def process_show_loan(self, user_data: Dict[str, Any]) -> str:
        """
        Muestra la oferta de préstamo
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            str: Oferta formateada
        """
        try:
            score_data = user_data.get('score_data')
            if not score_data:
                return "❌ Error: No hay datos de análisis"
            
            return report_generator.generate_loan_offer(score_data)
            
        except Exception as e:
            logger.error(f"Error mostrando préstamo: {str(e)}")
            return (
                "❌ Error generando oferta\n\n"
                "Por favor intenta de nuevo más tarde."
            )
    
    def process_confirm_loan(self) -> str:
        """Genera mensaje de confirmación de solicitud"""
        return report_generator.generate_success_message()
    
    async def handle_message(self, phone: str, text: str) -> str:
        """
        Maneja el mensaje entrante y actualiza el estado de la conversación
        
        Args:
            phone: Número de teléfono del usuario
            text: Mensaje de texto enviado por el usuario
            
        Returns:
            str: Respuesta generada para el usuario
        """
        # Obtener estado actual del usuario
        current_state = await firebase_manager.get_conversation_state(phone)
        
        # Validar entrada del usuario
        is_valid, processed_input = self.validate_input(current_state, text)
        
        if not is_valid:
            return self.get_error_message(current_state)
        
        # Obtener siguiente estado
        next_state = self.get_next_state(current_state, processed_input)
        
        # Actualizar estado del usuario
        firebase_manager.update_user_state(phone, next_state)
        
        # Obtener mensaje de respuesta
        response_message = self.get_next_message(next_state, {"phone": phone, "input": processed_input})
        
        # Procesar estados especiales
        if next_state == self.STATES['SHOW_REPORT']:
            response_message = await self.process_show_report({"phone": phone})
        elif next_state == self.STATES['SHOW_LOAN']:
            response_message = self.process_show_loan({"phone": phone})
        elif next_state == self.STATES['CONFIRM_LOAN']:
            response_message = self.process_confirm_loan()
        
        return response_message

# Instancia global
conversation_flow = ConversationFlow()
