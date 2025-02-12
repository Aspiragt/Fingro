"""
Módulo para manejar el flujo de conversación con usuarios
"""
from typing import Dict, Any, Optional
import logging
from app.models.financial_model import financial_model
from app.views.financial_report import report_generator
from app.external_apis.maga import CanalComercializacion
from app.services.whatsapp_service import WhatsAppService
from app.database.firebase import firebase_manager

logger = logging.getLogger(__name__)

class ConversationFlow:
    """Maneja el flujo de conversación con usuarios"""
    
    def __init__(self, whatsapp_service: WhatsAppService):
        """
        Inicializa el manejador de conversación
        
        Args:
            whatsapp_service: Servicio de WhatsApp para enviar mensajes
        """
        self.whatsapp = whatsapp_service
        
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
            user_input: Entrada opcional del usuario
            
        Returns:
            str: Siguiente estado
        """
        if current_state == self.STATES['START']:
            return self.STATES['GET_CROP']
            
        elif current_state == self.STATES['GET_CROP']:
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

    async def handle_message(self, phone_number: str, message: str):
        """
        Procesa un mensaje entrante de WhatsApp
        
        Args:
            phone_number: Número de teléfono del remitente
            message: Contenido del mensaje
        """
        try:
            # Normalizar mensaje
            message = message.lower().strip()
            
            # Comando de reinicio
            if message in ['reiniciar', 'reset', 'comenzar', 'inicio']:
                user_data = {
                    'state': self.STATES['START'],
                    'data': {}
                }
                await firebase_manager.update_user_state(phone_number, user_data)
                welcome_message = self.get_welcome_message()
                await self.whatsapp.send_message(phone_number, welcome_message)
                return
            
            # Obtener o crear datos del usuario
            try:
                user_data = await firebase_manager.get_conversation_state(phone_number)
            except Exception as e:
                logger.error(f"Error obteniendo datos del usuario: {str(e)}")
                error_message = (
                    "Lo siento, ha ocurrido un error. Por favor intenta nuevamente "
                    "o contacta a soporte si el problema persiste."
                )
                await self.whatsapp.send_message(phone_number, error_message)
                return
                
            if not user_data:
                user_data = {
                    'state': self.STATES['START'],
                    'data': {}
                }
                
            current_state = user_data['state']
            
            # Si es nuevo usuario o conversación terminada, reiniciar
            if current_state == self.STATES['START'] or current_state == self.STATES['DONE']:
                # Actualizar estado a GET_CROP
                user_data['state'] = self.STATES['GET_CROP']
                await firebase_manager.update_user_state(phone_number, user_data)
                welcome_message = self.get_welcome_message()
                await self.whatsapp.send_message(phone_number, welcome_message)
                return
                
            # Validar entrada del usuario
            is_valid, processed_value = self.validate_input(current_state, message)
            
            if not is_valid:
                # Enviar mensaje de error
                error_message = self.get_error_message(current_state)
                await self.whatsapp.send_message(phone_number, error_message)
                return
                
            # Guardar dato procesado
            user_data['data'][current_state] = processed_value
            
            # Obtener siguiente estado
            next_state = self.get_next_state(current_state, message)
            user_data['state'] = next_state
            
            # Si llegamos a SHOW_REPORT, generar reporte
            if next_state == self.STATES['SHOW_REPORT']:
                report = report_generator.generate_report(user_data['data'])
                await self.whatsapp.send_message(phone_number, report)
                
                # Preguntar si quiere préstamo
                loan_message = "¿Te gustaría solicitar un préstamo para este proyecto? (SI/NO)"
                await self.whatsapp.send_message(phone_number, loan_message)
                
            # Si llegamos a SHOW_LOAN, mostrar oferta
            elif next_state == self.STATES['SHOW_LOAN']:
                loan_offer = report_generator.generate_loan_offer(user_data['data'])
                await self.whatsapp.send_message(phone_number, loan_offer)
                
                # Preguntar si confirma
                confirm_message = "¿Deseas proceder con la solicitud del préstamo? (SI/NO)"
                await self.whatsapp.send_message(phone_number, confirm_message)
                
            # Si llegamos a DONE después de confirmar préstamo
            elif next_state == self.STATES['DONE'] and current_state == self.STATES['CONFIRM_LOAN']:
                if processed_value:  # Si confirmó el préstamo
                    final_message = (
                        "¡Excelente! 🎉 Tu solicitud de préstamo ha sido registrada.\n\n"
                        "Pronto un asesor se pondrá en contacto contigo para continuar el proceso. 👨‍💼"
                    )
                else:
                    final_message = (
                        "Entiendo. Si cambias de opinión o necesitas más información, "
                        "no dudes en contactarnos nuevamente. ¡Que tengas un excelente día! 👋"
                    )
                await self.whatsapp.send_message(phone_number, final_message)
                
            # Si llegamos a DONE sin confirmar préstamo
            elif next_state == self.STATES['DONE']:
                final_message = (
                    "Gracias por usar FinGro. Si necesitas analizar otro proyecto "
                    "o tienes más preguntas, ¡no dudes en escribirnos! 👋"
                )
                await self.whatsapp.send_message(phone_number, final_message)
                
            # Para cualquier otro estado, enviar siguiente pregunta
            else:
                next_message = self.get_next_message(next_state, user_data['data'])
                await self.whatsapp.send_message(phone_number, next_message)
            
            # Guardar datos actualizados
            await firebase_manager.update_user_state(phone_number, user_data)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            error_message = (
                "Lo siento, ha ocurrido un error. Por favor intenta nuevamente "
                "o contacta a soporte si el problema persiste."
            )
            await self.whatsapp.send_message(phone_number, error_message)

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

# Instancia global
conversation_flow = ConversationFlow(WhatsAppService())
