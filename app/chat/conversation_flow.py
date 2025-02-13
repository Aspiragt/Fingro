"""
Módulo para manejar el flujo de conversación con usuarios
"""
from typing import Dict, Any, Optional
import logging
from app.models.financial_model import financial_model
from app.views.financial_report import report_generator
from app.external_apis.maga_precios import CanalComercializacion, maga_precios_client
from app.services.whatsapp_service import WhatsAppService
from app.database.firebase import firebase_manager
from app.utils.text import normalize_text, parse_area, format_number, parse_yes_no, parse_channel, parse_irrigation, parse_department

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
            if 'crop' not in user_data or 'area' not in user_data:
                raise ValueError("Faltan datos del cultivo")
                
            # Preparar datos para el análisis
            analysis_data = {
                'crop': user_data['crop'],
                'area': float(user_data['area']),
                'commercialization': user_data.get('channel', CanalComercializacion.MAYORISTA),
                'irrigation': user_data.get('irrigation', 'ninguno'),
                'location': user_data.get('location', 'Guatemala')
            }
            
            # Generar análisis financiero
            financial_data = await financial_model.analyze_project(analysis_data)
            
            if not financial_data:
                raise ValueError("Error generando análisis financiero")

            # Guardar datos del análisis
            user_data['analysis'] = financial_data
            
            # Formatear reporte
            crop = financial_data['cultivo'].capitalize()
            area = financial_data['area']
            rendimiento = round(financial_data['rendimiento_por_ha'])
            ingresos = round(financial_data['ingresos_totales'])
            costos = round(financial_data['costos_siembra'])
            utilidad = round(financial_data['utilidad'])
            
            mensaje = (
                f"✨ {crop} - {area} hectáreas\n\n"
                
                f"💰 Resumen:\n"
                f"•⁠  ⁠Ingresos: Q{ingresos:,}\n"
                f"•⁠  ⁠Costos: Q{costos:,}\n"
                f"•⁠  ⁠Ganancia: Q{utilidad:,}\n\n"
            )

            # Agregar mensaje según la rentabilidad
            if utilidad > 0:
                mensaje += (
                    f"✅ ¡Su proyecto es rentable!\n\n"
                    f"¿Le gustaría que le ayude a solicitar un préstamo? 🤝\n\n"
                    f"Responda SI o NO 👇"
                )
            else:
                mensaje += (
                    f"⚠️ Con los precios actuales, necesita ajustes.\n\n"
                    f"💡 Le sugiero:\n"
                    f"1. Usar riego para mejorar rendimiento\n"
                    f"2. Buscar mejores precios de venta\n"
                    f"3. Reducir costos de producción"
                )
            
            return mensaje
            
        except Exception as e:
            logger.error(f"Error generando reporte financiero: {str(e)}")
            raise

    def calculate_loan_amount(self, user_data: Dict[str, Any]) -> Optional[float]:
        """
        Calcula el monto del préstamo basado en el proyecto
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            float: Monto del préstamo o None si no se puede calcular
        """
        try:
            # Obtener datos básicos
            cultivo = normalize_text(user_data.get('crop', ''))
            area = user_data.get('area', 0)  # En hectáreas
            channel = user_data.get('channel', '')
            irrigation = user_data.get('irrigation', '')
            
            # Obtener costos de producción
            costos = maga_precios_client.get_costos_cultivo(cultivo)
            if not costos:
                return None
                
            # Costo base por hectárea
            costo_base = costos.get('costo_por_hectarea', 0)
            
            # Ajustes por sistema de riego
            factores_riego = {
                'goteo': 1.2,  # 20% más por sistema de goteo
                'aspersion': 1.15,  # 15% más por aspersión
                'gravedad': 1.1,  # 10% más por gravedad
                'temporal': 1.0  # Sin ajuste para temporal
            }
            factor_riego = factores_riego.get(irrigation, 1.0)
            
            # Ajustes por canal de comercialización
            factores_canal = {
                'exportacion': 1.3,  # 30% más para exportación
                'mayorista': 1.2,  # 20% más para mayorista
                'cooperativa': 1.15,  # 15% más para cooperativa
                'mercado_local': 1.0  # Sin ajuste para mercado local
            }
            factor_canal = factores_canal.get(channel, 1.0)
            
            # Calcular monto total
            monto = costo_base * area * factor_riego * factor_canal
            
            # Redondear a miles
            monto = round(monto / 1000) * 1000
            
            return monto
            
        except Exception as e:
            logger.error(f"Error calculando monto: {str(e)}")
            return None
    
    def process_show_loan(self, user_data: Dict[str, Any]) -> str:
        """Procesa y muestra la oferta de préstamo"""
        try:
            # Obtener datos
            cultivo = user_data.get('crop', '').lower()
            area = user_data.get('area_original', 0)
            unit = user_data.get('area_unit', '')
            channel = user_data.get('channel', '')
            irrigation = user_data.get('irrigation', '')
            location = user_data.get('location', '')
            
            # Calcular préstamo
            monto = self.calculate_loan_amount(user_data)
            if not monto:
                return (
                    "Lo siento, no pudimos calcular un préstamo para su proyecto 😔\n\n"
                    "Por favor intente de nuevo con otros datos o escriba 'inicio' "
                    "para hacer otra consulta."
                )
            
            # Obtener costos y precios
            costos = maga_precios_client.get_costos_cultivo(cultivo)
            precios = maga_precios_client.get_precios_cultivo(cultivo, channel)
            
            # Formatear números
            monto_str = format_number(monto)
            cuota = format_number(monto * 0.12)  # 12% mensual aproximado
            
            # Calcular rendimiento esperado
            rendimiento = costos.get('rendimiento_por_hectarea', 0)
            area_ha = user_data.get('area', 0)  # En hectáreas
            produccion = rendimiento * area_ha
            precio_q = precios.get('precio_actual', 0)
            ingreso = produccion * precio_q
            
            # Formatear producción
            produccion_str = format_number(produccion)
            ingreso_str = format_number(ingreso)
            
            # Actualizar estado
            user_data['state'] = self.STATES['GET_LOAN_RESPONSE']
            user_data['loan_amount'] = monto
            
            # Construir mensaje
            return (
                f"¡Buenas noticias! 🎉\n\n"
                f"Con base en su proyecto:\n"
                f"- {cultivo.capitalize()} en {location} 🌱\n"
                f"- {format_number(area)} {unit} de terreno\n"
                f"- Riego por {irrigation} 💧\n"
                f"- Venta en {channel} 🚛\n\n"
                f"Producción esperada:\n"
                f"- {produccion_str} quintales de {cultivo} 📦\n"
                f"- Ingresos de Q{ingreso_str} 💰\n\n"
                f"Le podemos ofrecer:\n"
                f"- Préstamo de Q{monto_str} 💸\n"
                f"- Cuota de Q{cuota} al mes 📅\n"
                f"- 12 meses de plazo 🗓️\n"
                f"- Incluye asistencia técnica 🌿\n\n"
                f"¿Le interesa continuar con la solicitud? 🤝"
            )
            
        except Exception as e:
            logger.error(f"Error generando oferta: {str(e)}")
            return (
                "Lo siento, hubo un error al generar su oferta 😔\n\n"
                "Por favor intente de nuevo o escriba 'inicio' para hacer otra consulta."
            )

    def validate_yes_no(self, response: str) -> bool:
        """Valida respuestas sí/no de forma flexible"""
        if not response:
            return False
            
        # Normalizar respuesta
        response = response.lower().strip()
        
        # Lista de respuestas válidas
        valid_yes = ['si', 'sí', 's', 'yes', 'y']
        valid_no = ['no', 'n']
        
        return response in valid_yes or response in valid_no

    def get_yes_no(self, response: str) -> Optional[bool]:
        """Obtiene valor booleano de respuesta sí/no"""
        if not self.validate_yes_no(response):
            return None
            
        valid_yes = ['si', 'sí', 's', 'yes', 'y']
        clean_response = response.strip().lower()
        
        return clean_response in valid_yes

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
                    "1. Mercado local 🏪\n"
                    "2. Mayorista 🚛\n"
                    "3. Cooperativa 🤝\n"
                    "4. Exportación ✈️"
                )
            
            # Guardar canal
            user_data['channel'] = channel
            
            # Verificar si el cultivo es típicamente de exportación
            cultivo = normalize_text(user_data.get('crop', ''))
            if channel == 'exportacion' and cultivo not in maga_precios_client.export_crops:
                return (
                    f"El {cultivo} no es común para exportación 🤔\n"
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
            return self.process_show_loan(user_data)
            
        except Exception as e:
            logger.error(f"Error procesando ubicación: {str(e)}")
            return "Hubo un error. Por favor intente de nuevo 🙏"

    def process_show_loan(self, user_data: Dict[str, Any]) -> str:
        """Procesa y muestra la oferta de préstamo"""
        try:
            # Obtener datos
            cultivo = user_data.get('crop', '').lower()
            area = user_data.get('area_original', 0)
            unit = user_data.get('area_unit', '')
            channel = user_data.get('channel', '')
            irrigation = user_data.get('irrigation', '')
            location = user_data.get('location', '')
            
            # Calcular préstamo
            monto = self.calculate_loan_amount(user_data)
            if not monto:
                return "Lo siento, no pudimos calcular un préstamo para su proyecto 😔"
            
            # Formatear números
            monto_str = format_number(monto)
            cuota = format_number(monto * 0.12)  # 12% mensual aproximado
            
            # Calcular rendimiento esperado
            rendimiento = maga_precios_client.get_costos_cultivo(cultivo).get('rendimiento_por_hectarea', 0)
            area_ha = user_data.get('area', 0)  # En hectáreas
            produccion = rendimiento * area_ha
            precio_q = maga_precios_client.get_precios_cultivo(cultivo, channel).get('precio_actual', 0)
            ingreso = produccion * precio_q
            
            # Formatear producción
            produccion_str = format_number(produccion)
            ingreso_str = format_number(ingreso)
            
            # Actualizar estado
            user_data['state'] = self.STATES['GET_LOAN_RESPONSE']
            user_data['loan_amount'] = monto
            
            # Construir mensaje
            return (
                f"¡Buenas noticias! 🎉\n\n"
                f"Con base en su proyecto:\n"
                f"- {cultivo.capitalize()} en {location} 🌱\n"
                f"- {format_number(area)} {unit} de terreno\n"
                f"- Riego por {irrigation} 💧\n"
                f"- Venta en {channel} 🚛\n\n"
                f"Producción esperada:\n"
                f"- {produccion_str} quintales de {cultivo} 📦\n"
                f"- Ingresos de Q{ingreso_str} 💰\n\n"
                f"Le podemos ofrecer:\n"
                f"- Préstamo de Q{monto_str} 💸\n"
                f"- Cuota de Q{cuota} al mes 📅\n"
                f"- 12 meses de plazo 🗓️\n"
                f"- Incluye asistencia técnica 🌿\n\n"
                f"¿Le interesa continuar con la solicitud? 🤝"
            )
            
        except Exception as e:
            logger.error(f"Error generando oferta: {str(e)}")
            return "Lo siento, hubo un error al generar su oferta 😔"

# Instancia global
conversation_flow = ConversationFlow(WhatsAppService())
