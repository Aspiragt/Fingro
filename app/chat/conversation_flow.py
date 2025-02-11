"""
Módulo para manejar el flujo de la conversación
"""
import logging
import random
from typing import Dict, Any, Tuple, List
from app.utils.constants import ConversationState, MESSAGES, VALID_RESPONSES
from app.database.firebase import firebase_manager
from app.analysis.scoring import FingroScoring

logger = logging.getLogger(__name__)

class ConversationManager:
    """Maneja el flujo de la conversación con el usuario"""
    
    def __init__(self):
        """Inicializa el manejador de conversación"""
        self.scoring = FingroScoring()
        
        # Variaciones de mensajes para respuestas más naturales
        self.message_variations = {
            'greeting': [
                "¡Hola {}! ",
                "¡Qué gusto verte {}! ",
                "¡Bienvenido de nuevo {}! ",
                "¡Hola {}! Me alegra verte "
            ],
            'thanks': [
                "¡Gracias {}! ",
                "¡Excelente {}! ",
                "¡Perfecto {}! ",
                "¡Muy bien {}! "
            ],
            'continue': [
                "Continuemos con tu solicitud...",
                "Sigamos con el proceso...",
                "Avancemos con tu evaluación...",
                "Procedamos con tu solicitud..."
            ]
        }
    
    def _get_personalized_message(self, message_type: str, name: str = None) -> str:
        """Obtiene una variación aleatoria del mensaje y la personaliza con el nombre"""
        variations = self.message_variations.get(message_type, [""])
        message = random.choice(variations)
        return message.format(name if name else "")
    
    def handle_message(self, phone: str, message: str) -> Tuple[str, List[str]]:
        """
        Maneja el mensaje del usuario y retorna la respuesta apropiada
        """
        try:
            # Obtener estado actual
            user_state = firebase_manager.get_user_state(phone)
            current_state = user_state.get('state', ConversationState.INICIO)
            user_data = user_state.get('data', {})
            user_name = user_state.get('name')
            
            # Verificar comandos especiales
            if message.lower() in ['reiniciar', 'reset']:
                firebase_manager.reset_conversation(phone)
                return "Conversación reiniciada. ¿En qué puedo ayudarte?", []
            
            # Si es un saludo y tenemos el nombre, personalizar respuesta
            if current_state == ConversationState.INICIO and user_name:
                greeting = self._get_personalized_message('greeting', user_name)
                return f"{greeting}\n{MESSAGES[current_state]}", []
            
            # Procesar respuesta según el estado actual
            next_state, response = self._process_state(current_state, message, user_data)
            
            # Si la respuesta es válida, actualizar estado
            if next_state:
                firebase_manager.update_user_state(phone, next_state, user_data)
                
                # Si llegamos al final, calcular y guardar score
                if next_state == ConversationState.FINALIZADO:
                    score_data = self.scoring.calculate_score(user_data)
                    firebase_manager.save_fingro_score(phone, score_data)
                    user_data['score_data'] = score_data
                    
                    # Generar mensaje final con los datos
                    if callable(MESSAGES[ConversationState.FINALIZADO]):
                        response = MESSAGES[ConversationState.FINALIZADO](user_data)
            
            return response, []
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return "Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo.", []
    
    def _process_state(self, current_state: str, message: str, user_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Procesa el mensaje según el estado actual y retorna el siguiente estado y respuesta
        """
        message = message.lower().strip()
        
        if current_state == ConversationState.INICIO:
            user_data['cultivo'] = message
            return ConversationState.CULTIVO, MESSAGES[ConversationState.CULTIVO]
            
        elif current_state == ConversationState.CULTIVO:
            try:
                hectareas = float(message.replace(',', '.'))
                if hectareas <= 0:
                    return None, "Por favor, ingresa un número válido mayor a 0."
                user_data['hectareas'] = hectareas
                return ConversationState.HECTAREAS, MESSAGES[ConversationState.HECTAREAS]
            except ValueError:
                return None, "Por favor, ingresa solo el número de hectáreas (ejemplo: 2.5)."
                
        elif current_state == ConversationState.HECTAREAS:
            if message not in VALID_RESPONSES[ConversationState.RIEGO]:
                options = ", ".join(VALID_RESPONSES[ConversationState.RIEGO])
                return None, f"Por favor, selecciona una opción válida: {options}"
            user_data['riego'] = message
            return ConversationState.RIEGO, MESSAGES[ConversationState.RIEGO]
            
        elif current_state == ConversationState.RIEGO:
            if message not in VALID_RESPONSES[ConversationState.COMERCIALIZACION]:
                options = ", ".join(VALID_RESPONSES[ConversationState.COMERCIALIZACION])
                return None, f"Por favor, selecciona una opción válida: {options}"
            user_data['comercializacion'] = message
            return ConversationState.COMERCIALIZACION, MESSAGES[ConversationState.COMERCIALIZACION]
            
        elif current_state == ConversationState.COMERCIALIZACION:
            user_data['ubicacion'] = message
            return ConversationState.UBICACION, MESSAGES[ConversationState.UBICACION]
            
        elif current_state == ConversationState.UBICACION:
            return ConversationState.FINALIZADO, MESSAGES[ConversationState.FINALIZADO](user_data)
            
        return None, "Lo siento, no entendí tu mensaje. ¿Podrías intentarlo de nuevo?"

# Instancia global
conversation_manager = ConversationManager()
