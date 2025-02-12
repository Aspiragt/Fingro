"""
Módulo para manejar el flujo de conversación con usuarios
"""
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import asyncio
from app.models.financial_model import financial_model
from app.views.financial_report import report_generator
from app.external_apis.maga import CanalComercializacion
from app.database.firebase import firebase_manager, FirebaseError
from app.external_apis.maga_precios import maga_api
from app.utils.text import normalize_crop, sanitize_data
from app.analysis.financial import ProyectoAgricola, financial_analyzer

logger = logging.getLogger(__name__)

class ConversationState:
    """Estado de la conversación"""
    def __init__(self, state: str = 'START', data: Dict[str, Any] = None):
        self.state = state
        self.data = data or {}
        self.last_interaction = datetime.now()
        self.session_id = None
        
    def is_expired(self, timeout: timedelta = timedelta(minutes=30)) -> bool:
        """Verifica si la conversación ha expirado"""
        return datetime.now() - self.last_interaction > timeout
        
    def update(self, state: Optional[str] = None, **kwargs):
        """Actualiza el estado"""
        if state:
            self.state = state
        self.data.update(kwargs)
        self.last_interaction = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado a diccionario"""
        return {
            'state': self.state,
            'data': self.data,
            'last_interaction': self.last_interaction.isoformat(),
            'session_id': self.session_id
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Crea un estado desde un diccionario"""
        state = cls(
            state=data.get('state', 'START'),
            data=data.get('data', {})
        )
        state.last_interaction = datetime.fromisoformat(
            data.get('last_interaction', datetime.now().isoformat())
        )
        state.session_id = data.get('session_id')
        return state

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
            '4': 'temporal',
            # Texto exacto
            'gravedad': 'gravedad',
            'aspersion': 'aspersion',
            'aspersión': 'aspersion',
            'goteo': 'goteo',
            'temporal': 'temporal',
            # Variaciones comunes
            'por gravedad': 'gravedad',
            'por aspersion': 'aspersion',
            'por aspersión': 'aspersion',
            'por goteo': 'goteo',
            'lluvia': 'temporal',
            'natural': 'temporal',
            'ninguno': 'temporal'
        }
    
    async def handle_message(self, phone: str, message: str) -> str:
        """
        Maneja un mensaje entrante
        
        Args:
            phone: Número de teléfono del usuario
            message: Mensaje recibido
            
        Returns:
            str: Respuesta al usuario
        """
        try:
            # Obtener o crear estado
            state = await self._get_state(phone)
            
            # Verificar timeout
            if state.is_expired():
                await self._reset_state(phone)
                return "👋 ¡Hola de nuevo! Tu sesión anterior expiró. Empecemos de nuevo:\n\n¿Qué cultivo planeas sembrar?"
            
            # Procesar mensaje
            message = message.strip().lower()
            
            # Verificar comandos especiales
            if message in self.SPECIAL_COMMANDS:
                new_state = self.SPECIAL_COMMANDS[message]
                if new_state == 'HELP':
                    return self._get_help_message(state.state)
                state.update(state='START')
                await self._save_state(phone, state)
                return "👋 ¡Empecemos de nuevo!\n\n¿Qué cultivo planeas sembrar?"
            
            # Procesar según el estado actual
            response = await self._process_state(state, message)
            
            # Guardar estado actualizado
            await self._save_state(phone, state)
            
            return response
            
        except FirebaseError as e:
            logger.error(f"Error de Firebase: {str(e)}")
            return "😕 Lo siento, estamos teniendo problemas técnicos. Por favor, intenta más tarde."
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return "😕 Hubo un error inesperado. Por favor, intenta de nuevo o escribe 'reiniciar'."
    
    async def _process_state(self, state: ConversationState, message: str) -> str:
        """Procesa el mensaje según el estado actual"""
        try:
            if state.state == 'START' or state.state == 'GET_CROP':
                # Normalizar y validar cultivo
                cultivo = normalize_crop(message)
                state.update('GET_AREA', cultivo=cultivo)
                return "📏 ¿Cuántas hectáreas planeas sembrar?"
                
            elif state.state == 'GET_AREA':
                try:
                    area = float(message.replace(',', '.'))
                    if area <= 0:
                        return "❌ El área debe ser mayor a 0. Intenta de nuevo:"
                    if area > 1000:
                        return "❌ El área parece muy grande. Por favor verifica e intenta de nuevo:"
                    state.update('GET_CHANNEL', area=area)
                    return ("🏪 ¿Cómo planeas comercializar tu cosecha?\n\n"
                           "1. Mayorista\n"
                           "2. Cooperativa\n"
                           "3. Exportación\n"
                           "4. Mercado Local")
                except ValueError:
                    return "❌ Por favor ingresa un número válido de hectáreas:"
                    
            elif state.state == 'GET_CHANNEL':
                channel = self.channel_mapping.get(message)
                if not channel:
                    return ("❌ Por favor selecciona una opción válida:\n\n"
                           "1. Mayorista\n"
                           "2. Cooperativa\n"
                           "3. Exportación\n"
                           "4. Mercado Local")
                state.update('GET_IRRIGATION', channel=channel)
                return ("💧 ¿Qué sistema de riego utilizarás?\n\n"
                       "1. Gravedad\n"
                       "2. Aspersión\n"
                       "3. Goteo\n"
                       "4. Temporal (lluvia)")
                       
            elif state.state == 'GET_IRRIGATION':
                irrigation = self.irrigation_mapping.get(message)
                if not irrigation:
                    return ("❌ Por favor selecciona una opción válida:\n\n"
                           "1. Gravedad\n"
                           "2. Aspersión\n"
                           "3. Goteo\n"
                           "4. Temporal (lluvia)")
                state.update('GET_LOCATION', irrigation=irrigation)
                return "📍 ¿En qué departamento está ubicado el terreno?"
                
            elif state.state == 'GET_LOCATION':
                # Aquí podríamos validar contra una lista de departamentos
                state.update('SHOW_REPORT', location=message)
                
                # Crear proyecto y analizar
                proyecto = ProyectoAgricola(
                    cultivo=state.data['cultivo'],
                    hectareas=state.data['area'],
                    precio_actual=maga_api.get_precio(state.data['cultivo']),
                    metodo_riego=state.data['irrigation'],
                    ubicacion={'department': state.data['location']}
                )
                
                analysis = await financial_analyzer.analizar_proyecto(
                    proyecto,
                    session_id=state.session_id
                )
                
                # Generar reporte
                report = report_generator.generate_report(analysis)
                state.update('ASK_LOAN', analysis=analysis)
                
                return (f"{report}\n\n"
                       "¿Te gustaría solicitar un préstamo para este proyecto? (sí/no)")
                       
            elif state.state == 'ASK_LOAN':
                if message in ['si', 'sí', 'yes', 'dale']:
                    state.update('SHOW_LOAN')
                    return ("💰 Basado en tu análisis, podrías calificar para un préstamo.\n\n"
                           "¿Deseas que te contacte un asesor? (sí/no)")
                else:
                    state.update('DONE')
                    return "👍 ¡Gracias por usar FinGro! Si necesitas otro análisis, escribe 'reiniciar'."
                    
            elif state.state == 'SHOW_LOAN':
                if message in ['si', 'sí', 'yes', 'dale']:
                    state.update('DONE')
                    return ("✅ ¡Perfecto! Un asesor te contactará pronto.\n\n"
                           "Si necesitas otro análisis, escribe 'reiniciar'.")
                else:
                    state.update('DONE')
                    return "👍 ¡Gracias por usar FinGro! Si necesitas otro análisis, escribe 'reiniciar'."
            
            else:
                state.update('START')
                return "👋 ¡Bienvenido a FinGro!\n\n¿Qué cultivo planeas sembrar?"
                
        except Exception as e:
            logger.error(f"Error en _process_state: {str(e)}")
            raise
    
    async def _get_state(self, phone: str) -> ConversationState:
        """Obtiene el estado de la conversación"""
        try:
            data = await firebase_manager.get_conversation_state(phone)
            if data:
                return ConversationState.from_dict(data)
            return ConversationState()
        except Exception as e:
            logger.error(f"Error obteniendo estado: {str(e)}")
            raise
            
    async def _save_state(self, phone: str, state: ConversationState):
        """Guarda el estado de la conversación"""
        try:
            await firebase_manager.update_user_state(phone, state.to_dict())
        except Exception as e:
            logger.error(f"Error guardando estado: {str(e)}")
            raise
            
    async def _reset_state(self, phone: str):
        """Reinicia el estado de la conversación"""
        try:
            state = ConversationState()
            await self._save_state(phone, state)
        except Exception as e:
            logger.error(f"Error reiniciando estado: {str(e)}")
            raise
    
    def _get_help_message(self, current_state: str) -> str:
        """Obtiene el mensaje de ayuda según el estado actual"""
        help_messages = {
            'GET_CROP': "🌱 Por favor ingresa el tipo de cultivo que planeas sembrar, por ejemplo: maíz, frijol, papa, etc.",
            'GET_AREA': "📏 Ingresa el número de hectáreas que planeas sembrar. Debe ser un número mayor a 0.",
            'GET_CHANNEL': "🏪 Selecciona cómo planeas vender tu cosecha: mayorista, cooperativa, exportación o mercado local.",
            'GET_IRRIGATION': "💧 Indica el sistema de riego que usarás: gravedad, aspersión, goteo o temporal (lluvia).",
            'GET_LOCATION': "📍 Ingresa el departamento donde está ubicado el terreno.",
            'default': "👋 FinGro te ayuda a analizar la viabilidad de tu proyecto agrícola. Escribe 'reiniciar' para comenzar."
        }
        return help_messages.get(current_state, help_messages['default'])

# Instancia global
conversation_flow = ConversationFlow()
