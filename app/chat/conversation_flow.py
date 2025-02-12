"""
Módulo para manejar el flujo de conversación con usuarios
"""
from typing import Dict, Any, Optional
import logging
from app.models.financial_model import financial_model
from app.views.financial_report import report_generator
from app.external_apis.maga import CanalComercializacion
from app.database.firebase import firebase_manager
from app.external_apis.maga_precios import maga_api

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
        
        # Comandos especiales
        self.SPECIAL_COMMANDS = {
            'reiniciar': 'START',
            'menu': 'START',
            'ayuda': 'HELP',
            'hola': 'START'
        }
        
        # Mapeo de canales de comercialización
        self.channel_mapping = {
            # Números
            '1': CanalComercializacion.MAYORISTA,
            '2': CanalComercializacion.COOPERATIVA, 
            '3': CanalComercializacion.EXPORTACION,
            '4': CanalComercializacion.MERCADO_LOCAL,
            # Texto exacto
            'mayorista': CanalComercializacion.MAYORISTA,
            'cooperativa': CanalComercializacion.COOPERATIVA,
            'exportacion': CanalComercializacion.EXPORTACION,
            'exportación': CanalComercializacion.EXPORTACION,
            'mercado local': CanalComercializacion.MERCADO_LOCAL,
            # Variaciones comunes
            'mayor': CanalComercializacion.MAYORISTA,
            'coop': CanalComercializacion.COOPERATIVA,
            'export': CanalComercializacion.EXPORTACION,
            'mercado': CanalComercializacion.MERCADO_LOCAL,
            'local': CanalComercializacion.MERCADO_LOCAL
        }
        
        # Mapeo de sistemas de riego
        self.irrigation_mapping = {
            # Números
            '1': 'gravedad',
            '2': 'aspersion',
            '3': 'goteo',
            '4': 'ninguno',
            # Texto exacto
            'gravedad': 'gravedad',
            'aspersion': 'aspersion',
            'aspersión': 'aspersion',
            'goteo': 'goteo',
            'ninguno': 'ninguno',
            # Variaciones comunes
            'por gravedad': 'gravedad',
            'por aspersion': 'aspersion',
            'por aspersión': 'aspersion',
            'por goteo': 'goteo',
            'no': 'ninguno',
            'nada': 'ninguno',
            'sin riego': 'ninguno'
        }
        
        # Mapeo de respuestas afirmativas/negativas
        self.yes_no_mapping = {
            # Afirmativo
            'si': True,
            'sí': True,
            'yes': True,
            'ok': True,
            'dale': True,
            'va': True,
            'simon': True,
            'simón': True,
            'claro': True,
            # Negativo
            'no': False,
            'nel': False,
            'nop': False,
            'nope': False
        }
    
    def get_welcome_message(self) -> str:
        """Retorna mensaje de bienvenida"""
        return (
            "👋 ¡Hola! Soy FinGro, tu asistente financiero agrícola.\n\n"
            "Te ayudaré a analizar la rentabilidad de tu proyecto y "
            "obtener financiamiento. 🌱💰\n\n"
            "Para empezar, *¿qué cultivo planeas sembrar?* 🌾\n\n"
            "Por ejemplo: maíz, frijol, papa, tomate, etc."
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
            return (
                "¿Cuántas hectáreas planeas sembrar? 🌱\n\n"
                "Puedes responder con números o texto, por ejemplo:\n"
                "- 2.5\n"
                "- Dos y media\n"
                "- 2 1/2"
            )
            
        elif current_state == self.STATES['GET_CHANNEL']:
            return (
                "¿Cómo planeas comercializar tu producto? 🏪\n\n"
                "Puedes elegir:\n"
                "1. Mayorista\n"
                "2. Cooperativa\n"
                "3. Exportación\n"
                "4. Mercado Local\n\n"
                "Responde con el número o nombre de tu elección"
            )
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            return (
                "¿Qué sistema de riego utilizarás? 💧\n\n"
                "Puedes elegir:\n"
                "1. Gravedad\n"
                "2. Aspersión\n"
                "3. Goteo\n"
                "4. Ninguno\n\n"
                "Responde con el número o nombre del sistema"
            )
            
        elif current_state == self.STATES['GET_LOCATION']:
            return "¿En qué departamento está ubicado el terreno? 📍"
            
        return "❌ Estado no válido"
    
    async def validate_input(self, current_state: str, user_input: str) -> tuple:
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
            # Buscar el cultivo en MAGA
            try:
                # Normalizar y limpiar la entrada
                user_input = user_input.strip().lower()
                logger.info(f"Validando cultivo (entrada original): {user_input}")
                
                # Intentar búsqueda
                crop_info = await maga_api.search_crop(user_input)
                logger.info(f"Resultado búsqueda: {crop_info}")
                
                if crop_info:
                    logger.info(f"Cultivo encontrado: {crop_info['nombre']}")
                    return True, {
                        'nombre': crop_info['nombre'],
                        'precio': crop_info['precio'],
                        'unidad': crop_info['unidad']
                    }
                else:
                    # Si no se encuentra, intentar con variaciones comunes
                    variations = [
                        user_input.replace('maiz', 'maíz'),
                        user_input.replace('frijol', 'frijol_negro'),
                        user_input.replace('platano', 'plátano'),
                    ]
                    
                    for variation in variations:
                        if variation != user_input:
                            logger.info(f"Intentando con variación: {variation}")
                            crop_info = await maga_api.search_crop(variation)
                            if crop_info:
                                logger.info(f"Cultivo encontrado con variación: {crop_info['nombre']}")
                                return True, {
                                    'nombre': crop_info['nombre'],
                                    'precio': crop_info['precio'],
                                    'unidad': crop_info['unidad']
                                }
                    
                    logger.warning(f"Cultivo no encontrado: {user_input}")
                    return False, None
                    
            except Exception as e:
                logger.error(f"Error buscando cultivo en MAGA: {str(e)}")
                return False, None
                
        elif current_state == self.STATES['GET_AREA']:
            # Primero intentar convertir directamente
            try:
                area = float(user_input.replace(',', '.'))
                if 0.1 <= area <= 100:
                    return True, area
            except:
                pass
            
            # Si falla, intentar procesar texto
            try:
                # Limpiar texto
                text = user_input.lower().replace('hectareas', '').replace('hectáreas', '')
                text = text.replace('ha', '').strip()
                
                # Procesar fracciones
                if '/' in text:
                    num, den = map(float, text.split('/'))
                    area = num/den
                    if 0.1 <= area <= 100:
                        return True, area
                
                # Mapeo de números escritos
                number_mapping = {
                    'media': 0.5,
                    'un': 1, 'una': 1,
                    'dos': 2,
                    'tres': 3,
                    'cuatro': 4,
                    'cinco': 5,
                    'seis': 6,
                    'siete': 7,
                    'ocho': 8,
                    'nueve': 9,
                    'diez': 10
                }
                
                for num_text, value in number_mapping.items():
                    if num_text in text:
                        if 'y media' in text:
                            value += 0.5
                        if 0.1 <= value <= 100:
                            return True, value
                
            except Exception as e:
                logger.error(f"Error procesando área en texto: {str(e)}")
            
            return False, None
            
        elif current_state == self.STATES['GET_CHANNEL']:
            # Buscar en el mapeo de canales
            for key, value in self.channel_mapping.items():
                if key in user_input:
                    return True, value
            return False, None
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            # Buscar en el mapeo de sistemas de riego
            for key, value in self.irrigation_mapping.items():
                if key in user_input:
                    return True, value
            return False, None
            
        elif current_state == self.STATES['GET_LOCATION']:
            if len(user_input) > 0:
                return True, user_input
            return False, None
            
        elif current_state in [self.STATES['ASK_LOAN'], self.STATES['CONFIRM_LOAN']]:
            # Buscar en el mapeo de sí/no
            for key, value in self.yes_no_mapping.items():
                if key in user_input:
                    return True, value
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
                "❌ No encontré ese cultivo en nuestra base de datos.\n"
                "Por favor, intenta con otro nombre o verifica la ortografía."
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
        try:
            # Obtener estado actual del usuario
            current_state = await firebase_manager.get_conversation_state(phone)
            
            # Normalizar entrada
            text = text.lower().strip()
            
            # Verificar comandos especiales
            if text in self.SPECIAL_COMMANDS:
                current_state = {
                    'state': self.STATES[self.SPECIAL_COMMANDS[text]],
                    'data': {}
                }
                await firebase_manager.update_user_state(phone, current_state)
                return self.get_welcome_message()
            
            # Si es un usuario nuevo o no tiene estado, inicializar
            if not current_state or 'state' not in current_state:
                current_state = {
                    'state': self.STATES['START'],
                    'data': {}
                }
                await firebase_manager.update_user_state(phone, current_state)
                return self.get_welcome_message()
            
            # Validar entrada del usuario
            is_valid, processed_input = await self.validate_input(current_state['state'], text)
            
            if not is_valid:
                if current_state['state'] == self.STATES['GET_CROP']:
                    return (
                        "❌ No encontré ese cultivo en nuestra base de datos.\n"
                        "Por favor, intenta con otro nombre o verifica la ortografía."
                    )
                return "❌ Entrada no válida. Por favor intenta de nuevo."
            
            # Obtener siguiente estado
            next_state = self.get_next_state(current_state['state'], text)
            
            # Actualizar datos del usuario
            if processed_input is not None:
                current_state['data'][current_state['state']] = processed_input
            current_state['state'] = next_state
            
            # Actualizar estado del usuario
            await firebase_manager.update_user_state(phone, current_state)
            
            # Obtener mensaje de respuesta
            response_message = self.get_next_message(next_state, current_state['data'])
            
            # Procesar estados especiales
            if next_state == self.STATES['SHOW_REPORT']:
                response_message = await self.process_show_report(current_state['data'])
            elif next_state == self.STATES['SHOW_LOAN']:
                response_message = self.process_show_loan(current_state['data'])
            elif next_state == self.STATES['CONFIRM_LOAN']:
                response_message = self.process_confirm_loan()
            
            return response_message
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            return "❌ Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo."
    
# Instancia global
conversation_flow = ConversationFlow()
