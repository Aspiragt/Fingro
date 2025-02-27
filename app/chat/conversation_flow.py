"""
Módulo para manejar el flujo de conversación con usuarios
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import unidecode

from app.database.firebase import firebase_manager
from app.external_apis.maga_precios import (
    MagaPreciosClient,
    CanalComercializacion,
    maga_precios_client
)
from app.utils.text import (
    normalize_text,
    parse_yes_no,
    parse_area,
    format_number,
    parse_channel,
    parse_irrigation,
    parse_department
)
from app.utils.currency import format_currency
from app.models.financial_model import financial_model
from app.views.financial_report import report_generator
from app.services.whatsapp_service import WhatsAppService
from app.utils.text import normalize_text, parse_area, format_number, parse_channel, parse_irrigation, parse_department

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
            'SHOW_ANALYSIS': 'show_analysis',
            'ASK_LOAN': 'ask_loan',
            'SHOW_LOAN': 'show_loan',
            'GET_LOAN_RESPONSE': 'get_loan_response',
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
            'goteo', 'aspersion', 'gravedad', 'temporal'
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
                "1. Goteo",
                "2. Aspersión",
                "3. Gravedad",
                "4. Ninguno (depende de lluvia)"
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
            if self.validate_yes_no(user_input):
                return True, self.get_yes_no(user_input)
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
            return self.STATES['SHOW_ANALYSIS']
            
        elif current_state == self.STATES['SHOW_ANALYSIS']:
            return self.STATES['ASK_LOAN']
            
        elif current_state == self.STATES['ASK_LOAN']:
            if processed_value:  # Si respondió SI
                return self.STATES['SHOW_LOAN']
            return self.STATES['DONE']  # Si respondió NO
            
        elif current_state == self.STATES['SHOW_LOAN']:
            return self.STATES['CONFIRM_LOAN']
            
        elif current_state == self.STATES['CONFIRM_LOAN']:
            if processed_value:  # Si respondió SI
                return self.STATES['DONE']
            return self.STATES['ASK_LOAN']  # Si respondió NO
            
        elif current_state == self.STATES['GET_LOAN_RESPONSE']:
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
            
            # Comando de reinicio o saludo inicial
            if message in ['reiniciar', 'reset', 'comenzar', 'inicio', 'hola']:
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
            if next_state == self.STATES['SHOW_ANALYSIS']:
                try:
                    # Mostrar reporte y preguntar por préstamo
                    report = await self.process_show_analysis(user_data['data'])
                    await self.whatsapp.send_message(phone_number, report)
                    
                    # Actualizar estado a ASK_LOAN
                    user_data['state'] = self.STATES['ASK_LOAN']
                    await firebase_manager.update_user_state(phone_number, user_data)
                    
                    loan_message = (
                        "¿Le gustaría que le ayude a solicitar un préstamo para este proyecto? 🤝\n\n"
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
                        "Por favor intente de nuevo."
                    )
                    await self.whatsapp.send_message(phone_number, error_message)
                    # Regresar a ASK_LOAN
                    user_data['state'] = self.STATES['ASK_LOAN']
                
            elif next_state == self.STATES['CONFIRM_LOAN']:
                try:
                    confirm_message = self.process_confirm_loan()
                    await self.whatsapp.send_message(phone_number, confirm_message)
                except Exception as e:
                    logger.error(f"Error confirmando préstamo: {str(e)}")
                    error_message = (
                        "Lo siento, ha ocurrido un error procesando su solicitud. "
                        "Por favor intente de nuevo."
                    )
                    await self.whatsapp.send_message(phone_number, error_message)
                    # Regresar a ASK_LOAN
                    user_data['state'] = self.STATES['ASK_LOAN']
                
            elif next_state == self.STATES['DONE']:
                if current_state == self.STATES['GET_LOAN_RESPONSE']:
                    confirm_message = self.process_end_conversation(user_data['data'])
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
            if next_state not in [self.STATES['SHOW_LOAN'], self.STATES['CONFIRM_LOAN'], self.STATES['DONE']]:
                next_message = self.get_next_message(next_state, user_data)
                await self.whatsapp.send_message(phone_number, next_message)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            error_message = (
                "Lo siento, ha ocurrido un error. Por favor intenta nuevamente "
                "o contacta a soporte si el problema persiste."
            )
            await self.whatsapp.send_message(phone_number, error_message)

    async def process_state(self, state: str, message: str, user_data: Dict[str, Any]) -> Any:
        """Procesa un mensaje según el estado actual"""
        try:
            # Comandos especiales
            if message.lower() == 'inicio':
                user_data.clear()
                return None
                
            if message.lower() == 'ayuda':
                return None
                
            # Procesar según estado
            if state == self.STATES['GET_CROP']:
                return self.process_crop(message)
                
            elif state == self.STATES['GET_AREA']:
                return self.process_area(message)
                
            elif state == self.STATES['GET_CHANNEL']:
                return self.process_channel(message)
                
            elif state == self.STATES['GET_IRRIGATION']:
                return self.process_irrigation(message)
                
            elif state == self.STATES['GET_LOCATION']:
                return self.process_location(message)
                
            elif state == self.STATES['ASK_LOAN']:
                return self.process_loan_question(message)
                
            elif state == self.STATES['GET_LOAN_RESPONSE']:
                return self.process_loan_response(user_data, message)
                
            return None
            
        except Exception as e:
            logger.error(f"Error procesando estado {state}: {str(e)}")
            return None
            
    def process_loan_question(self, message: str) -> str:
        """Procesa la respuesta a si quiere un préstamo"""
        result = self.get_yes_no(message)
        
        if result is None:
            return (
                "Por favor responda SI o NO.\n\n"
                "¿Le gustaría solicitar un préstamo? 🤝"
            )
            
        if not result:
            return (
                "Entiendo. Si cambia de opinión, puede escribir 'préstamo' "
                "en cualquier momento para revisar las opciones de financiamiento. 💡\n\n"
                "¿Hay algo más en que pueda ayudarle? 🤝"
            )
            
        return "Excelente, revisemos las opciones de préstamo disponibles... 📊"

    async def process_show_analysis(self, user_data: Dict[str, Any]) -> str:
        """
        Procesa y muestra el análisis financiero
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            str: Análisis financiero formateado
        """
        try:
            # Obtener datos básicos
            cultivo = user_data.get('crop', '')
            area = user_data.get('area', 0)  # En hectáreas
            irrigation = user_data.get('irrigation', '')
            channel = user_data.get('channel', '')
            
            if not cultivo or not area:
                raise ValueError("Por favor ingrese el cultivo y el área")
            
            # Obtener costos y precios
            costos = maga_precios_client.calcular_costos_totales(cultivo, area, irrigation)
            precios = maga_precios_client.get_precios_cultivo(cultivo, channel)
            rendimiento = maga_precios_client.get_rendimiento_cultivo(cultivo, irrigation)
            
            # Calcular métricas
            precio_actual = precios['precio']
            ingresos = rendimiento * area * precio_actual
            ganancia = ingresos - costos['total']
            
            # Guardar datos para préstamo
            user_data['financial_analysis'] = {
                'costos': costos['total'],
                'ingresos': ingresos,
                'ganancia': ganancia,
                'rendimiento': rendimiento
            }
            
            # Formatear números
            ingresos_str = format_currency(ingresos)
            costos_str = format_currency(costos['total'])
            ganancia_str = format_currency(ganancia)
            rendimiento_str = format_number(rendimiento * area)
            
            # Construir mensaje
            mensaje = (
                f"✨ *Su Cultivo de {cultivo.capitalize()}*\n\n"
                f"🌱 Área sembrada: {area} hectáreas\n"
                f"💧 Tipo de riego: {irrigation.capitalize()}\n"
                f"🏪 Dónde venderá: {channel}\n\n"
                f"📊 *¿Cuánto producirá?*\n"
                f"• Cosecha esperada: {rendimiento_str} quintales\n"
                f"• Precio por quintal: {format_currency(precio_actual)}\n\n"
                f"💰 *¿Cuánto invertirá y ganará?*\n"
                f"• Gastos fijos: {format_currency(costos['fijos'])}\n"
                f"• Gastos por hectárea: {format_currency(costos['variables'])}\n"
                f"• Total de gastos: {costos_str}\n"
                f"• Total de ventas: {ingresos_str}\n"
                f"• Ganancia esperada: {ganancia_str}\n\n"
            )
            
            # Agregar recomendación
            if ganancia > 0:
                mensaje += "✅ *¿Qué le parece?*\n"
                if ganancia > costos['total'] * 0.3:  # 30% de rentabilidad
                    mensaje += "¡Este proyecto se ve muy bueno! Podría ganar más del 30% de lo invertido 🌟\n\n"
                else:
                    mensaje += "Este proyecto puede funcionar. La ganancia es positiva 👍\n\n"
            else:
                mensaje += "⚠️ *¿Qué le parece?*\n"
                mensaje += "Hay que revisar bien los números. Los costos son mayores que los ingresos esperados 🔍\n\n"
            
            mensaje += "¿Le gustaría ver qué opciones de préstamo tenemos para su cultivo? 💳"
            
            return mensaje
            
        except ValueError as e:
            logger.error(f"Error generando análisis financiero: {str(e)}")
            return (
                "Disculpe, no pude hacer los cálculos para su cultivo 😔\n\n"
                "Esto puede ser porque:\n"
                "• Falta información del cultivo\n"
                "• No tenemos datos de ese cultivo todavía\n"
                "• Hubo un error en los cálculos\n\n"
                "¿Le gustaría intentar de nuevo? 🔄"
            )
            
        except Exception as e:
            logger.error(f"Error procesando reporte: {str(e)}")
            return (
                "Disculpe, tuvimos un problema al hacer los cálculos 😔\n"
                "¿Le gustaría intentar de nuevo? 🔄"
            )

    def get_crop_cycle(self, crop: str) -> Dict[str, Any]:
        """Obtiene información del ciclo del cultivo"""
        cycles = {
            'maiz': {
                'duracion_meses': 4,
                'cosechas_por_año': 2,
                'meses_siembra': [5, 11],  # Mayo y Noviembre
                'tipo': 'anual',
                'nombre': 'maíz'
            },
            'frijol': {
                'duracion_meses': 3,
                'cosechas_por_año': 3,
                'meses_siembra': [3, 6, 9],  # Marzo, Junio, Septiembre
                'tipo': 'anual',
                'nombre': 'frijol'
            },
            'cafe': {
                'duracion_meses': 8,
                'cosechas_por_año': 1,
                'meses_siembra': [5],  # Mayo
                'tipo': 'permanente',
                'nombre': 'café'
            }
        }
        return cycles.get(crop, {
            'duracion_meses': 4,
            'cosechas_por_año': 2,
            'meses_siembra': [5, 11],
            'tipo': 'anual',
            'nombre': crop
        })

    def get_risk_factors(self, irrigation: str, channel: str) -> Dict[str, float]:
        """Calcula factores de riesgo basados en riego y canal de venta"""
        # Factores por sistema de riego
        irrigation_factors = {
            'goteo': 1.2,     # +20% por sistema de goteo
            'aspersion': 1.15, # +15% por aspersión
            'gravedad': 1.1,   # +10% por gravedad
            'temporal': 1.0    # Sin ajuste para temporal
        }
        
        # Factores por canal de comercialización
        channel_factors = {
            'exportacion': 1.3,    # +30% para exportación
            'mayorista': 1.2,      # +20% para mayorista
            'cooperativa': 1.15,   # +15% para cooperativa
            'mercado_local': 1.0   # Sin ajuste para mercado local
        }
        
        return {
            'riego': irrigation_factors.get(irrigation, 1.0),
            'canal': channel_factors.get(channel, 1.0)
        }

    def calculate_loan_amount(self, user_data: Dict[str, Any]) -> float:
        """Calcula el monto del préstamo basado en hectáreas"""
        area = user_data.get('area', 0)
        
        if area <= 10:
            return 4000
        elif area <= 15:
            return 8000
        else:
            return 16000

    def process_show_loan(self, user_data: Dict[str, Any]) -> str:
        """Procesa y muestra la oferta de préstamo"""
        try:
            # Obtener datos básicos
            cultivo = user_data.get('crop', '')
            ciclo = self.get_crop_cycle(cultivo)
            financial = user_data.get('financial_analysis', {})
            
            # Calcular monto del préstamo (80% de los costos totales)
            costos = financial.get('costos', 0)
            monto_prestamo = costos * 0.8
            
            # Calcular plazo basado en ciclo del cultivo
            plazo_meses = ciclo.get('duracion_meses', 4)
            
            # Calcular cuota mensual (tasa del 1% mensual)
            tasa_mensual = 0.01  # 12% anual
            cuota = (monto_prestamo * tasa_mensual) / (1 - (1 + tasa_mensual) ** -plazo_meses)
            
            # Guardar datos del préstamo
            user_data['loan_offer'] = {
                'monto': monto_prestamo,
                'plazo': plazo_meses,
                'cuota': cuota
            }
            
            # Calcular ejemplos prácticos
            quintales_semilla = monto_prestamo / 200  # Asumiendo Q200 por quintal de semilla
            area_adicional = quintales_semilla * 0.5  # Asumiendo 0.5 hectáreas por quintal
            
            # Formatear mensaje
            mensaje = (
                f"💰 *Préstamo para su {cultivo}*\n\n"
                f"Con este préstamo usted podría:\n"
                f"• Comprar {int(quintales_semilla)} quintales de semilla 🌱\n"
                f"• Sembrar {int(area_adicional)} cuerdas más ✨\n\n"
                f"*Detalles del préstamo:*\n"
                f"• Le prestamos: {format_currency(monto_prestamo)}\n"
                f"• Plazo: {plazo_meses} meses (una cosecha)\n"
                f"• Pago mensual: {format_currency(cuota)}\n\n"
                f"¿Le gustaría continuar con la solicitud? 🤝\n"
                f"Responda SI o NO"
            )
            
            return mensaje
            
        except Exception as e:
            logger.error(f"Error calculando monto de préstamo: {str(e)}")
            return (
                "Disculpe, hubo un problema al calcular su préstamo 😔\n"
                "¿Le gustaría intentar de nuevo? 🔄"
            )
            
    def process_loan_response(self, user_data: Dict[str, Any], response: str) -> str:
        """Procesa la respuesta a la oferta de préstamo"""
        # Normalizar respuesta
        response = unidecode(response.lower().strip())
        
        # Lista de respuestas válidas
        respuestas_si = ['si', 'sí', 's', 'yes', 'claro', 'dale', 'ok', 'okay']
        respuestas_no = ['no', 'n', 'nel', 'nop', 'nope']
        
        if response in respuestas_si:
            user_data['state'] = self.STATES['CONFIRM_LOAN']
            return self.process_confirm_loan()
        elif response in respuestas_no:
            user_data['state'] = self.STATES['DONE']
            return (
                "Entiendo 👍 Si cambia de opinión o necesita más información, "
                "estoy aquí para ayudarle.\n\n"
                "Puede escribir 'inicio' para hacer una nueva consulta."
            )
        else:
            return (
                "Por favor responda SI o NO para continuar con la solicitud del préstamo 🤔\n"
                "¿Le gustaría proceder con la solicitud?"
            )
            
    def process_location(self, user_data: Dict[str, Any], response: str) -> str:
        """
        Procesa la respuesta de la ubicación
        
        Args:
            user_data: Datos del usuario
            response: Respuesta del usuario
            
        Returns:
            str: Mensaje de respuesta
        """
        try:
            # Validar departamento
            department = parse_department(response)
            if not department:
                return (
                    "Por favor ingrese un departamento válido.\n"
                    "Por ejemplo: Guatemala, Escuintla, Petén, etc.\n\n"
                    "¿En qué departamento está su terreno? 📍"
                )
            
            # Guardar ubicación
            user_data['location'] = department
            
            # Verificar si el cultivo es adecuado para la región
            cultivo = normalize_text(user_data.get('crop', ''))
            if not maga_precios_client.is_crop_suitable(cultivo, department):
                return (
                    f"El {cultivo} no es muy común en {department} 🤔\n"
                    f"¿Está seguro que quiere sembrar aquí? Escoja una opción:\n\n"
                    f"1. Sí, tengo experiencia en la región\n"
                    f"2. No, mejor consulto otros cultivos"
                )
            
            # Siguiente paso
            return self.process_financial_analysis(user_data)
            
        except Exception as e:
            logger.error(f"Error procesando ubicación: {str(e)}")
            return "Hubo un error. Por favor intente de nuevo 🙏"

    def process_financial_analysis(self, user_data: Dict[str, Any]) -> str:
        """Procesa y muestra el análisis financiero"""
        try:
            # Obtener datos básicos
            cultivo = user_data.get('crop', '')
            area = user_data.get('area', 0)
            channel = user_data.get('channel', '')
            irrigation = user_data.get('irrigation', '')
            location = user_data.get('location', '')
            
            # Calcular análisis financiero
            financial = self.calculate_financial_analysis(cultivo, area, channel, irrigation)
            if not financial:
                return self.handle_error(user_data, Exception("No se pudo calcular el análisis financiero"), "financial")
                
            # Guardar análisis en datos de usuario
            user_data['financial_analysis'] = financial
            
            # Formatear y mostrar análisis
            return self.format_financial_analysis(financial, user_data)
            
        except Exception as e:
            logger.error(f"Error procesando análisis financiero: {str(e)}")
            return (
                "Disculpe, hubo un error al procesar su análisis 😔\n"
                "¿Le gustaría intentar de nuevo? 🔄"
            )

    def validate_yes_no(self, response: str) -> bool:
        """Valida respuestas sí/no de forma flexible"""
        if not response:
            return False
            
        # Normalizar respuesta
        response = self._normalize_text(response)
        
        # Variaciones positivas
        positivas = [
            'si', 'sí', 's', 'yes', 'ok', 'dale', 'va', 'bueno', 
            'esta bien', 'está bien', 'claro', 'por supuesto',
            'adelante', 'hagamoslo', 'hagámoslo', 'me interesa'
        ]
        
        # Variaciones negativas
        negativas = [
            'no', 'nel', 'nop', 'nope', 'n', 'mejor no',
            'no gracias', 'paso', 'ahorita no', 'después',
            'en otro momento', 'todavía no', 'todavia no'
        ]
        
        if any(p in response for p in positivas):
            return True
            
        if any(n in response for n in negativas):
            return False
            
        # Si no coincide con ninguna, pedir aclaración
        return None

    def get_yes_no(self, response: str) -> Optional[bool]:
        """Obtiene valor booleano de respuesta sí/no"""
        result = self.validate_yes_no(response)
        if result is None:
            return None
        return result

    def process_confirm_loan(self) -> str:
        """
        Procesa la confirmación del préstamo
        
        Returns:
            str: Mensaje de confirmación
        """
        return (
            "✨ *¡Excelente decisión!*\n\n"
            "Su solicitud de préstamo está siendo procesada.\n\n"
            "En las próximas 24 horas:\n"
            "• Revisaremos su solicitud 📋\n"
            "• Prepararemos los documentos 📄\n"
            "• Nos comunicaremos con usted 📱\n\n"
            "¿Tiene alguna pregunta mientras tanto? 🤝\n"
            "Estoy aquí para ayudarle."
        )

    def process_area(self, user_data: Dict[str, Any], response: str) -> str:
        """
        Procesa la respuesta del área de cultivo
        
        Args:
            user_data: Datos del usuario
            response: Respuesta del usuario
            
        Returns:
            str: Mensaje de respuesta
        """
        try:
            # Parsear área
            result = parse_area(response)
            if not result:
                return (
                    "Por favor ingrese el área con su unidad. Por ejemplo:\n"
                    "- 2 manzanas\n"
                    "- 1.5 hectáreas\n"
                    "- 3 mz\n"
                    "- 2.5 ha"
                )
            
            value, unit = result
            
            # Validar rango
            if value <= 0:
                return "El área debe ser mayor que 0. ¿Cuánto está sembrando? 🌱"
                
            if value > 1000:
                return "El área parece muy grande. ¿Puede confirmar la cantidad? 🤔"
            
            # Convertir a hectáreas si es necesario
            if unit == 'manzana':
                hectareas = value * 0.7
            else:
                hectareas = value
            
            # Guardar en datos de usuario
            user_data['area'] = hectareas
            user_data['area_original'] = value
            user_data['area_unit'] = unit
            
            # Siguiente pregunta
            return self.ask_channel(user_data)
            
        except Exception as e:
            logger.error(f"Error procesando área: {str(e)}")
            return "Hubo un error. Por favor intente de nuevo con el área que está sembrando 🌱"

    def process_channel(self, user_data: Dict[str, Any], response: str) -> str:
        """
        Procesa la respuesta del canal de comercialización
        
        Args:
            user_data: Datos del usuario
            response: Respuesta del usuario
            
        Returns:
            str: Mensaje de respuesta
        """
        try:
            # Validar canal
            channel = parse_channel(response)
            if not channel:
                return (
                    "Por favor escoja una opción válida:\n\n"
                    "1. Mercado local - En su comunidad\n"
                    "2. Mayorista - A distribuidores\n"
                    "3. Cooperativa - Con otros productores\n"
                    "4. Exportación - A otros países"
                )
            
            # Guardar canal
            user_data['channel'] = channel
            
            # Verificar si el cultivo es típicamente de exportación
            cultivo = normalize_text(user_data.get('crop', ''))
            if channel == 'exportacion' and cultivo not in maga_precios_client.export_crops:
                return (
                    f"El {cultivo} no es muy común para exportación 🤔\n"
                    f"¿Está seguro que quiere exportar? Escoja una opción:\n\n"
                    f"1. Sí, tengo comprador para exportación\n"
                    f"2. No, mejor escojo otro canal"
                )
            
            # Siguiente pregunta
            return self.ask_irrigation(user_data)
            
        except Exception as e:
            logger.error(f"Error procesando canal: {str(e)}")
            return "Hubo un error. Por favor intente de nuevo 🙏"

    def process_irrigation(self, user_data: Dict[str, Any], response: str) -> str:
        """
        Procesa la respuesta del sistema de riego
        
        Args:
            user_data: Datos del usuario
            response: Respuesta del usuario
            
        Returns:
            str: Mensaje de respuesta
        """
        try:
            # Validar sistema
            system = parse_irrigation(response)
            if not system:
                return (
                    "Por favor escoja una opción válida:\n\n"
                    "1. Goteo 💧\n"
                    "2. Aspersión 💦\n"
                    "3. Gravedad 🌊\n"
                    "4. Ninguno (depende de lluvia) 🌧️"
                )
            
            # Guardar sistema
            user_data['irrigation'] = system
            
            # Verificar si es temporal para cultivos que necesitan riego
            cultivo = normalize_text(user_data.get('crop', ''))
            if system == 'temporal' and cultivo in maga_precios_client.irrigated_crops:
                return (
                    f"El {cultivo} generalmente necesita riego para buenos resultados 🤔\n"
                    f"¿Está seguro que no usará ningún sistema de riego? Escoja una opción:\n\n"
                    f"1. Sí, solo dependeré de la lluvia\n"
                    f"2. No, mejor escojo un sistema de riego"
                )
            
            # Siguiente pregunta
            return self.ask_location(user_data)
            
        except Exception as e:
            logger.error(f"Error procesando sistema de riego: {str(e)}")
            return "Hubo un error. Por favor intente de nuevo 🙏"

    def ask_location(self, user_data: Dict[str, Any]) -> str:
        """Pregunta por la ubicación"""
        # Actualizar estado
        user_data['state'] = self.STATES['GET_LOCATION']
        
        cultivo = user_data.get('crop', '').lower()
        irrigation = user_data.get('irrigation', '')
        
        # Mapeo de sistemas a emojis
        irrigation_emojis = {
            'goteo': '💧',
            'aspersion': '💦',
            'gravedad': '🌊',
            'temporal': '🌧️'
        }
        
        # Mapeo de sistemas a nombres amigables
        irrigation_names = {
            'goteo': 'goteo',
            'aspersion': 'aspersión',
            'gravedad': 'gravedad',
            'temporal': 'temporal (lluvia)'
        }
        
        emoji = irrigation_emojis.get(irrigation, '')
        system_name = irrigation_names.get(irrigation, irrigation)
        
        return (
            f"Perfecto. Usará riego por {system_name} {emoji}\n\n"
            f"¿En qué departamento está su terreno?\n"
            f"Por ejemplo: Guatemala, Escuintla, etc."
        )

    def ask_irrigation(self, user_data: Dict[str, Any]) -> str:
        """Pregunta por el sistema de riego"""
        # Actualizar estado
        user_data['state'] = self.STATES['GET_IRRIGATION']
        
        cultivo = user_data.get('crop', '').lower()
        channel = user_data.get('channel', '')
        
        # Mapeo de canales a emojis
        channel_emojis = {
            'mercado_local': '🏪',
            'mayorista': '🚛',
            'cooperativa': '🤝',
            'exportacion': '✈️'
        }
        
        # Mapeo de canales a nombres amigables
        channel_names = {
            'mercado_local': 'mercado local',
            'mayorista': 'mayorista',
            'cooperativa': 'cooperativa',
            'exportacion': 'exportación'
        }
        
        emoji = channel_emojis.get(channel, '')
        channel_name = channel_names.get(channel, channel)
        
        return (
            f"Perfecto. Venderá su {cultivo} en {channel_name} {emoji}\n\n"
            f"¿Qué sistema de riego utilizarás? Escoja una opción:\n\n"
            f"1. Goteo 💧\n"
            f"2. Aspersión 💦\n"
            f"3. Gravedad 🌊\n"
            f"4. Ninguno (depende de lluvia) 🌧️"
        )

    def handle_error(self, user_data: Dict[str, Any], error: Exception, context: str) -> str:
        """
        Maneja errores de forma amigable y ofrece alternativas
        
        Args:
            user_data: Datos del usuario
            error: Error ocurrido
            context: Contexto del error (cultivo, area, etc)
            
        Returns:
            str: Mensaje de error amigable
        """
        logger.error(f"Error en {context}: {str(error)}")
        
        # Mensajes por contexto
        mensajes = {
            'crop': (
                "Lo siento, no pude procesar el cultivo indicado. 😕\n"
                "Por favor, escriba el nombre del cultivo que planea sembrar. "
                "Por ejemplo: maíz, frijol, café, etc. 🌱"
            ),
            'area': (
                "El área indicada no es válida. 😕\n"
                "Por favor indique el área en hectáreas o cuerdas. "
                "Por ejemplo: 2.5 o 4 🌾"
            ),
            'channel': (
                "Por favor seleccione una opción válida:\n\n"
                "1. Mayorista\n"
                "2. Cooperativa\n"
                "3. Exportación\n"
                "4. Mercado Local\n\n"
                "Responda con el número de su elección 🏪"
            ),
            'irrigation': (
                "Por favor seleccione una opción válida:\n\n"
                "1. Goteo\n"
                "2. Aspersión\n"
                "3. Gravedad\n"
                "4. Ninguno (depende de lluvia)\n\n"
                "Responda con el número de su elección 💧"
            ),
            'location': (
                "Lo siento, no reconozco ese departamento. 😕\n"
                "Por favor escriba el nombre del departamento donde está el terreno. "
                "Por ejemplo: Guatemala, Escuintla, etc. 📍"
            ),
            'financial': (
                "Lo siento, hubo un problema al generar su análisis. 😕\n"
                "¿Le gustaría intentar nuevamente? Responda SI o NO 🔄"
            ),
            'loan': (
                "Lo siento, hubo un problema al procesar su solicitud. 😕\n"
                "¿Le gustaría intentar nuevamente? Responda SI o NO 🔄"
            )
        }
        
        return mensajes.get(context, "Lo siento, hubo un error. ¿Podría intentar nuevamente? 🔄")

    def process_message(self, user_data: Dict[str, Any], message: str) -> str:
        """
        Procesa un mensaje del usuario
        
        Args:
            user_data: Datos del usuario
            message: Mensaje del usuario
            
        Returns:
            str: Respuesta al usuario
        """
        try:
            # Comandos especiales
            if message.lower() == 'inicio':
                user_data.clear()
                return self.start_conversation()
                
            if message.lower() == 'ayuda':
                return self.show_help(user_data)
            
            # Procesar según estado
            current_state = user_data.get('state', self.STATES['START'])
            
            if current_state == self.STATES['START']:
                return self.process_crop(user_data, message)
                
            elif current_state == self.STATES['GET_AREA']:
                return self.process_area(user_data, message)
                
            elif current_state == self.STATES['GET_CHANNEL']:
                return self.process_channel(user_data, message)
                
            elif current_state == self.STATES['GET_IRRIGATION']:
                return self.process_irrigation(user_data, message)
                
            elif current_state == self.STATES['GET_LOCATION']:
                return self.process_location(user_data, message)
                
            elif current_state == self.STATES['GET_LOAN_RESPONSE']:
                return self.process_loan_response(user_data, message)
                
            else:
                return self.handle_error(user_data, Exception("Estado inválido"), "critical")
                
        except Exception as e:
            return self.handle_error(user_data, e, "critical")
    
    def show_help(self, user_data: Dict[str, Any]) -> str:
        """Muestra mensaje de ayuda"""
        current_state = user_data.get('state', self.STATES['START'])
        
        # Mensajes de ayuda por estado
        help_messages = {
            self.STATES['START']: (
                "¡Bienvenido a FinGro! 👋\n\n"
                "Le ayudo a conseguir financiamiento para su siembra 🌱\n\n"
                "Para empezar, dígame qué cultivo está sembrando."
            ),
            self.STATES['GET_AREA']: (
                "Necesito saber el tamaño de su terreno.\n\n"
                "Puede usar:\n"
                "- Manzanas (2 manzanas)\n"
                "- Hectáreas (1.5 ha)\n"
                "- Cuerdas (3 cuerdas)"
            ),
            self.STATES['GET_CHANNEL']: (
                "¿Dónde piensa vender su cosecha?\n\n"
                "1. Mercado local - En su comunidad\n"
                "2. Mayorista - A distribuidores\n"
                "3. Cooperativa - Con otros productores\n"
                "4. Exportación - A otros países"
            ),
            self.STATES['GET_IRRIGATION']: (
                "¿Cómo riega sus cultivos?\n\n"
                "1. Goteo 💧\n"
                "2. Aspersión 💦\n"
                "3. Gravedad 🌊\n"
                "4. Ninguno (depende de lluvia) 🌧️"
            ),
            self.STATES['GET_LOCATION']: (
                "¿En qué departamento está su terreno?\n\n"
                "Por ejemplo:\n"
                "- Guatemala\n"
                "- Escuintla\n"
                "- Alta Verapaz"
            ),
            self.STATES['GET_LOAN_RESPONSE']: (
                "¿Desea continuar con la solicitud?\n\n"
                "- SI para continuar\n"
                "- NO para terminar\n\n"
                "Puede escribir 'inicio' para empezar de nuevo"
            )
        }
        
        return help_messages.get(current_state, (
            "Comandos disponibles:\n"
            "- 'inicio' para empezar de nuevo\n"
            "- 'ayuda' para ver opciones\n"
        ))

# Instancia global
conversation_flow = ConversationFlow(WhatsAppService())

def parse_yes_no(message: str) -> Optional[bool]:
    """
    Valida una respuesta si/no
    
    Args:
        message: Mensaje a validar
        
    Returns:
        bool: True si es sí, False si es no, None si es inválido
    """
    # Normalizar mensaje
    message = normalize_text(message)
    
    # Validar respuesta
    if message in ['si', 'sí', 's', 'yes', 'y', '1']:
        return True
        
    if message in ['no', 'n', '2']:
        return False
        
    return None

def process_loan_response(user_data: Dict[str, Any], message: str) -> bool:
    """Procesa la respuesta a la oferta de préstamo"""
    try:
        # Validar respuesta
        result = parse_yes_no(message)
        if result is None:
            raise ValueError("Por favor responda SI o NO")
            
        if result:
            user_data['loan_approved'] = True
            
        return result
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de préstamo: {str(e)}")
        raise
