"""
Módulo para manejar el flujo de conversación
"""
import logging
from typing import Dict, Any, Tuple, List
from datetime import datetime
from app.database.firebase import firebase_manager
from app.external_apis.maga import maga_api
from app.analysis.scoring import scoring

logger = logging.getLogger(__name__)

class ConversationManager:
    """Maneja el flujo de conversación con el usuario"""
    
    # Estados de la conversación
    STATES = {
        'START': 'start',
        'ASKING_CROP': 'asking_crop',
        'ASKING_AREA': 'asking_area',
        'ASKING_COMMERCIALIZATION': 'asking_commercialization',
        'ASKING_IRRIGATION': 'asking_irrigation',
        'ASKING_LOCATION': 'asking_location',
        'SHOWING_ANALYSIS': 'showing_analysis',
        'FINISHED': 'finished'
    }
    
    # Mensajes del bot
    MESSAGES = {
        'welcome': "¡Hola! 👋 Soy FinGro, tu asistente para acceder a financiamiento agrícola. ¿Qué cultivas? 🌱",
        'ask_area': "¿Cuántas hectáreas cultivas? 🌾",
        'ask_commercialization': "¿Cómo comercializas tu producto?\n1. Exportación\n2. Mercado local\n3. Venta directa\n4. Intermediario",
        'ask_irrigation': "¿Qué sistema de riego utilizas?\n1. Goteo\n2. Aspersión\n3. Gravedad\n4. Temporal",
        'ask_location': "¿En qué departamento está tu cultivo? 📍",
        'invalid_input': "Por favor, ingresa una respuesta válida 🤔",
        'processing': "Analizando tu información... ⏳",
        'error': "Hubo un error. Escribe 'reiniciar' para comenzar de nuevo 🔄"
    }
    
    def __init__(self):
        """Inicializa el manejador de conversación"""
        pass
    
    async def handle_message(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja un mensaje entrante y retorna la respuesta
        """
        try:
            # Normalizar mensaje
            message = message.strip().lower()
            
            # Comando de reinicio
            if message == 'reiniciar':
                firebase_manager.reset_conversation(phone)
                return self.MESSAGES['welcome'], []
            
            # Obtener estado actual
            state = await self._get_state(phone)
            
            # Procesar mensaje según el estado
            if state == self.STATES['START']:
                return await self._handle_start(phone, message)
            elif state == self.STATES['ASKING_CROP']:
                return await self._handle_crop(phone, message)
            elif state == self.STATES['ASKING_AREA']:
                return await self._handle_area(phone, message)
            elif state == self.STATES['ASKING_COMMERCIALIZATION']:
                return await self._handle_commercialization(phone, message)
            elif state == self.STATES['ASKING_IRRIGATION']:
                return await self._handle_irrigation(phone, message)
            elif state == self.STATES['ASKING_LOCATION']:
                return await self._handle_location(phone, message)
            else:
                # Estado no reconocido, reiniciar
                firebase_manager.reset_conversation(phone)
                return self.MESSAGES['welcome'], []
                
        except Exception as e:
            logger.error(f"Error manejando mensaje: {str(e)}")
            return self.MESSAGES['error'], []
    
    async def _get_state(self, phone: str) -> str:
        """
        Obtiene el estado actual de la conversación
        """
        state = firebase_manager.get_conversation_state(phone)
        if not state:
            # Nuevo usuario, inicializar estado
            state = {
                'state': self.STATES['ASKING_CROP'],
                'data': {},
                'created_at': datetime.now().isoformat()
            }
            firebase_manager.update_conversation_state(phone, state)
            return self.STATES['ASKING_CROP']
        
        return state.get('state', self.STATES['ASKING_CROP'])
    
    async def _update_state(self, phone: str, new_state: str, data: Dict[str, Any] = None) -> None:
        """
        Actualiza el estado de la conversación
        """
        state = firebase_manager.get_conversation_state(phone) or {}
        state['state'] = new_state
        if data:
            state['data'] = state.get('data', {})
            state['data'].update(data)
        state['updated_at'] = datetime.now().isoformat()
        
        firebase_manager.update_conversation_state(phone, state)
    
    async def _handle_crop(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja la respuesta del cultivo
        """
        # Guardar cultivo
        await self._update_state(phone, self.STATES['ASKING_AREA'], {'cultivo': message})
        
        # Obtener precios del cultivo
        prices = await maga_api.get_crop_prices(message)
        if prices:
            await self._update_state(phone, self.STATES['ASKING_AREA'], {'precios': prices})
        
        return self.MESSAGES['ask_area'], []
    
    async def _handle_area(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja la respuesta del área
        """
        try:
            area = float(message.replace('hectareas', '').replace('ha', '').strip())
            await self._update_state(phone, self.STATES['ASKING_COMMERCIALIZATION'], {'hectareas': area})
            return self.MESSAGES['ask_commercialization'], []
        except ValueError:
            return self.MESSAGES['invalid_input'], []
    
    async def _handle_commercialization(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja la respuesta de comercialización
        """
        commercialization_map = {
            '1': 'exportación',
            '2': 'mercado local',
            '3': 'directo',
            '4': 'intermediario'
        }
        
        commercialization = commercialization_map.get(message, message.lower())
        if commercialization not in commercialization_map.values():
            return self.MESSAGES['invalid_input'], []
        
        await self._update_state(phone, self.STATES['ASKING_IRRIGATION'], {'comercializacion': commercialization})
        return self.MESSAGES['ask_irrigation'], []
    
    async def _handle_irrigation(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja la respuesta del sistema de riego
        """
        irrigation_map = {
            '1': 'goteo',
            '2': 'aspersión',
            '3': 'gravedad',
            '4': 'temporal'
        }
        
        irrigation = irrigation_map.get(message, message.lower())
        if irrigation not in irrigation_map.values():
            return self.MESSAGES['invalid_input'], []
        
        await self._update_state(phone, self.STATES['ASKING_LOCATION'], {'riego': irrigation})
        return self.MESSAGES['ask_location'], []
    
    async def _handle_location(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja la respuesta de ubicación y genera análisis
        """
        # Guardar ubicación
        state = firebase_manager.get_conversation_state(phone)
        state['data']['ubicacion'] = message
        
        # Calcular Fingro Score
        score_result = scoring.calculate_score(state['data'])
        if score_result:
            state['data']['fingro_score'] = score_result
            firebase_manager.update_conversation_state(phone, state)
            
            # Generar mensaje de resultado
            score = score_result['fingro_score']
            prestamo = score_result['prestamo_recomendado']
            
            response = (
                f"¡Análisis completado! 📊\n\n"
                f"Tu Fingro Score es: {score}/100 ⭐\n"
                f"Préstamo recomendado: Q{prestamo:,.2f} 💰\n\n"
                f"¿Te gustaría solicitar el préstamo ahora? 🤝\n"
                f"1. Sí, quiero aplicar\n"
                f"2. No, tal vez después"
            )
            
            await self._update_state(phone, self.STATES['SHOWING_ANALYSIS'])
            return response, []
        else:
            return self.MESSAGES['error'], []

    async def _handle_start(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja el inicio de la conversación
        """
        return self.MESSAGES['welcome'], []

# Instancia global
conversation_manager = ConversationManager()
