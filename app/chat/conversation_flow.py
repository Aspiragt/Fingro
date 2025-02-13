"""
Módulo para manejar el flujo de conversación con usuarios
"""
from typing import Dict, Any, Optional
import logging
from app.models.financial_model import financial_model
from app.views.financial_report import report_generator
from app.external_apis.maga import CanalComercializacion, maga_api
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
        self.valid_crops = []  # Aceptar cualquier cultivo
        
        self.valid_channels = [
            CanalComercializacion.MAYORISTA,
            CanalComercializacion.COOPERATIVA,
            CanalComercializacion.EXPORTACION,
            CanalComercializacion.MERCADO_LOCAL
        ]
        
        self.valid_irrigation = [
            'gravedad', 'aspersion', 'goteo', 'ninguno'
        ]
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza el texto para comparación
        - Remueve tildes
        - Convierte a minúsculas
        - Remueve espacios extra
        """
        import unicodedata
        if not text:
            return ""
            
        # Convertir a string si no lo es
        text = str(text)
        
        # Normalizar NFD y eliminar diacríticos
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        # A minúsculas y remover espacios extra
        return text.lower().strip()

    def _is_similar_crop(self, input_crop: str, valid_crop: str) -> bool:
        """
        Compara si dos nombres de cultivos son similares
        - Ignora tildes
        - Ignora mayúsculas/minúsculas
        - Permite algunas variaciones comunes
        """
        input_norm = self._normalize_text(input_crop)
        valid_norm = self._normalize_text(valid_crop)
        
        # Mapa de variaciones comunes
        variations = {
            'maiz': ['mais', 'maíz', 'maices'],
            'frijol': ['frijoles', 'frijoles', 'frijol negro', 'frijol rojo'],
            'papa': ['papas', 'patata', 'patatas'],
            'tomate': ['tomates', 'jitomate'],
            'cafe': ['café', 'cafeto', 'cafetal'],
            'platano': ['plátano', 'platanos', 'plátanos', 'banano', 'bananos'],
            'limon': ['limón', 'limones', 'limonero'],
            'brocoli': ['brócoli', 'brocolis', 'brócolis']
        }
        
        # Revisar coincidencia directa
        if input_norm == valid_norm:
            return True
            
        # Revisar variaciones
        if valid_norm in variations and input_norm in variations[valid_norm]:
            return True
            
        return False

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
            return "¿Cuántas hectáreas planea sembrar? 🌱"
            
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
        if not user_input:
            return False, None

        # Normalizar input
        user_input = self._normalize_text(user_input)
            
        if current_state == self.STATES['GET_CROP']:
            return True, self._normalize_crop(user_input)
            
        elif current_state == self.STATES['GET_AREA']:
            try:
                area = float(user_input.replace(',', '.'))
                if 0.1 <= area <= 100:
                    return True, area
            except ValueError:
                pass
            return False, None
            
        elif current_state == self.STATES['GET_CHANNEL']:
            try:
                channel = int(user_input)
                if 1 <= channel <= 4:
                    return True, self.valid_channels[channel - 1]
            except ValueError:
                pass
            return False, None
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            try:
                irrigation = int(user_input)
                if 1 <= irrigation <= 4:
                    return True, self.valid_irrigation[irrigation - 1]
            except ValueError:
                pass
            return False, None
            
        elif current_state == self.STATES['GET_LOCATION']:
            # Validar que la ubicación tenga al menos 3 caracteres
            if len(user_input.strip()) >= 3:
                return True, user_input.strip().capitalize()
            return False, None
            
        elif current_state in [self.STATES['ASK_LOAN'], self.STATES['CONFIRM_LOAN']]:
            # Validar respuestas SI/NO
            user_input = user_input.lower().strip()
            if user_input.startswith(('si', 'sí', 's')):
                return True, True
            elif user_input.startswith(('no', 'n')):
                return True, False
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
        if current_state == self.STATES['GET_AREA']:
            return "❌ Por favor ingrese un número válido entre 0.1 y 100 hectáreas"
            
        elif current_state == self.STATES['GET_CHANNEL']:
            return "❌ Por favor seleccione una opción válida (1-4)"
            
        elif current_state == self.STATES['GET_IRRIGATION']:
            return "❌ Por favor seleccione una opción válida (1-4)"
            
        elif current_state == self.STATES['GET_LOCATION']:
            return "❌ Por favor ingrese el nombre de su municipio o departamento (mínimo 3 letras)"
            
        elif current_state in [self.STATES['ASK_LOAN'], self.STATES['CONFIRM_LOAN']]:
            return "❌ Por favor responda solamente SI o NO"
            
        return "❌ Respuesta no válida, por favor intente nuevamente"

    def get_next_state(self, current_state: str, user_input: str = None, processed_value: bool = None) -> str:
        """
        Obtiene el siguiente estado de la conversación
        
        Args:
            current_state: Estado actual
            user_input: Entrada opcional del usuario
            processed_value: Valor procesado para SI/NO
            
        Returns:
            str: Siguiente estado
        """
        if current_state == self.STATES['GET_CROP']:
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
            if processed_value:  # Si respondió SI
                return self.STATES['SHOW_LOAN']
            return self.STATES['DONE']  # Si respondió NO
            
        elif current_state == self.STATES['SHOW_LOAN']:
            return self.STATES['CONFIRM_LOAN']
            
        elif current_state == self.STATES['CONFIRM_LOAN']:
            return self.STATES['DONE']
            
        return self.STATES['GET_CROP']  # Estado por defecto

    def _normalize_crop(self, crop: str) -> str:
        """Normaliza el nombre del cultivo"""
        crop = self._normalize_text(crop)
        
        # Mapa de nombres normalizados
        crop_names = {
            'maiz': 'maíz',
            'frijo': 'frijol',
            'papa': 'papa',
            'tomate': 'tomate',
            'cafe': 'café',
            'platano': 'plátano',
            'limon': 'limón',
            'brocoli': 'brócoli'
        }
        
        # Buscar coincidencia parcial
        for normalized, full_name in crop_names.items():
            if crop.startswith(normalized):
                return full_name
                
        return crop.capitalize()
    
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
                # Limpiar caché de Firebase
                await firebase_manager.clear_user_cache(phone_number)
                
                user_data = {
                    'state': self.STATES['GET_CROP'],
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
                # Nuevo usuario, iniciar conversación
                user_data = {
                    'state': self.STATES['GET_CROP'],
                    'data': {}
                }
                await firebase_manager.update_user_state(phone_number, user_data)
                welcome_message = self.get_welcome_message()
                await self.whatsapp.send_message(phone_number, welcome_message)
                return
                
            current_state = user_data['state']
            logger.info(f"Estado actual: {current_state}, Mensaje: {message}")
            
            # Si conversación terminada, reiniciar
            if current_state == self.STATES['DONE']:
                user_data = {
                    'state': self.STATES['GET_CROP'],
                    'data': {}
                }
                await firebase_manager.update_user_state(phone_number, user_data)
                welcome_message = self.get_welcome_message()
                await self.whatsapp.send_message(phone_number, welcome_message)
                return
            
            # Validar entrada del usuario
            is_valid, processed_value = self.validate_input(current_state, message)
            logger.info(f"Validación: válido={is_valid}, valor={processed_value}")
            
            if not is_valid:
                # Enviar mensaje de error
                error_message = self.get_error_message(current_state)
                await self.whatsapp.send_message(phone_number, error_message)
                return
                
            # Actualizar datos del usuario
            if current_state == self.STATES['GET_CROP']:
                user_data['data']['crop'] = processed_value
            elif current_state == self.STATES['GET_AREA']:
                user_data['data']['area'] = processed_value
            elif current_state == self.STATES['GET_CHANNEL']:
                user_data['data']['channel'] = processed_value
            elif current_state == self.STATES['GET_IRRIGATION']:
                user_data['data']['irrigation'] = processed_value
            elif current_state == self.STATES['GET_LOCATION']:
                user_data['data']['location'] = processed_value
                
            # Obtener siguiente estado
            next_state = self.get_next_state(current_state, message, processed_value)
            
            # Procesar estado especial
            if next_state == self.STATES['SHOW_REPORT']:
                try:
                    # Mostrar reporte y preguntar por préstamo
                    report = await self.process_show_report(user_data['data'])
                    await self.whatsapp.send_message(phone_number, report)
                    
                    # Actualizar estado a ASK_LOAN
                    user_data['state'] = self.STATES['ASK_LOAN']
                    await firebase_manager.update_user_state(phone_number, user_data)
                    
                    loan_message = (
                        "Don(ña), ¿le gustaría que le ayude a solicitar un préstamo para este proyecto? 🤝\n\n"
                        "Responda SI o NO 👇"
                    )
                    await self.whatsapp.send_message(phone_number, loan_message)
                    return
                except Exception as e:
                    logger.error(f"Error procesando reporte: {str(e)}")
                    # Mantener el estado actual si hay error
                    error_message = (
                        "Lo siento, ha ocurrido un error generando su reporte. "
                        "Por favor intente nuevamente."
                    )
                    await self.whatsapp.send_message(phone_number, error_message)
                    return
                    
            # Actualizar estado
            user_data['state'] = next_state
            
            if next_state == self.STATES['SHOW_LOAN']:
                try:
                    loan_offer = self.process_show_loan(user_data['data'])
                    await self.whatsapp.send_message(phone_number, loan_offer)
                except ValueError as e:
                    logger.error(f"Error mostrando préstamo: {str(e)}")
                    error_message = str(e)
                    await self.whatsapp.send_message(phone_number, error_message)
                    # Regresar a ASK_LOAN
                    user_data['state'] = self.STATES['ASK_LOAN']
                except Exception as e:
                    logger.error(f"Error inesperado en préstamo: {str(e)}")
                    error_message = (
                        "Lo siento, ha ocurrido un error procesando su solicitud. "
                        "Por favor intente nuevamente."
                    )
                    await self.whatsapp.send_message(phone_number, error_message)
                    # Regresar a ASK_LOAN
                    user_data['state'] = self.STATES['ASK_LOAN']
                
            elif next_state == self.STATES['DONE']:
                if current_state == self.STATES['CONFIRM_LOAN']:
                    confirm_message = self.process_confirm_loan()
                    await self.whatsapp.send_message(phone_number, confirm_message)
                else:
                    await self.whatsapp.send_message(
                        phone_number,
                        "Gracias por usar FinGro. ¡Que tenga un excelente día! 👋\n\n"
                        "Puede escribir 'inicio' para comenzar una nueva consulta."
                    )
            
            # Guardar estado actualizado
            await firebase_manager.update_user_state(phone_number, user_data)
            
            # Si no es estado especial, mostrar siguiente mensaje
            if next_state not in [self.STATES['SHOW_LOAN'], self.STATES['DONE']]:
                next_message = self.get_next_message(next_state, user_data)
                await self.whatsapp.send_message(phone_number, next_message)
            
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
            # Preparar datos para el modelo financiero
            analysis_data = {
                'crop': user_data['crop'],
                'area': float(user_data['area']),
                'commercialization': user_data['channel'],
                'irrigation': user_data['irrigation'],
                'location': user_data['location']
            }
            
            # Analizar proyecto
            score_data = await financial_model.analyze_project(analysis_data)
            if not score_data:
                raise ValueError("Error generando análisis financiero")

            # Guardar datos del análisis
            user_data['analysis'] = analysis_data
            user_data['score_data'] = score_data

            # Generar reporte
            report = report_generator.generate_report(analysis_data, score_data)
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte financiero: {str(e)}")
            raise
    
    def process_show_loan(self, user_data: Dict[str, Any]) -> str:
        """
        Procesa y muestra la oferta de préstamo
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            str: Mensaje con oferta de préstamo
        """
        try:
            if 'score_data' not in user_data:
                raise ValueError("No hay datos de análisis")

            score_data = user_data['score_data']
            analysis_data = user_data['analysis']

            # Calcular monto del préstamo (80% del costo total)
            costo_total = score_data.get('costos_siembra', 0)
            monto_prestamo = costo_total * 0.8

            # Formatear mensaje
            mensaje = (
                f"🏦 *Oferta de Préstamo*\n\n"
                f"Para su cultivo de {analysis_data['crop']} en {analysis_data['location']}:\n\n"
                f"💰 Monto: Q{monto_prestamo:,.2f}\n"
                f"📅 Plazo: 12 meses\n"
                f"💸 Tasa: 12% anual\n\n"
                f"¿Desea proceder con la solicitud? Responda SI o NO 👇"
            )
            return mensaje

        except Exception as e:
            logger.error(f"Error procesando préstamo: {str(e)}")
            raise ValueError(f"Error: {str(e)}")

    def process_confirm_loan(self) -> str:
        """
        Procesa la confirmación del préstamo
        
        Returns:
            str: Mensaje de confirmación
        """
        return (
            "✅ ¡Excelente! En breve uno de nuestros asesores se pondrá en contacto "
            "con usted para finalizar su solicitud.\n\n"
            "Gracias por confiar en FinGro. ¡Que tenga un excelente día! 👋\n\n"
            "Puede escribir 'inicio' para comenzar una nueva consulta."
        )

# Instancia global
conversation_flow = ConversationFlow(WhatsAppService())
