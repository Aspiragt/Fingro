"""
Módulo para manejar el flujo de conversación
"""
import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

from app.database.firebase import firebase_manager
from app.external_apis.maga import maga_api
from app.analysis.scoring import scoring_service
from app.services.whatsapp_service import WhatsAppService
from app.models.conversation import Conversation, ConversationContext, Message
from app.utils.constants import ConversationState, MESSAGES
from app.utils.text import (
    normalize_text,
    normalize_crop,
    normalize_irrigation,
    normalize_commercialization,
    normalize_yes_no
)
from app.views.financial_report import report_generator

logger = logging.getLogger(__name__)

class ConversationManager:
    """Maneja el flujo de conversación con el usuario"""
    
    def __init__(self):
        """Inicializa el manejador de conversación"""
        self.whatsapp = WhatsAppService()
    
    async def handle_message(self, phone: str, message: str) -> None:
        """
        Maneja un mensaje entrante y retorna la respuesta
        
        Args:
            phone: Número de teléfono del usuario
            message: Mensaje recibido
        """
        try:
            # Normalizar mensaje
            message = message.strip()
            
            # Manejar comando de reinicio
            if message.lower() == "reiniciar":
                await self._handle_reset(phone)
                return
            
            # Obtener estado actual
            conversation_data = await firebase_manager.get_conversation_state(phone)
            current_state = conversation_data.get('state', ConversationState.INITIAL.value)
            user_data = conversation_data.get('data', {})
            
            # Procesar mensaje según estado
            handler = self._get_state_handler(current_state)
            if not handler:
                logger.error(f"Estado no manejado: {current_state}")
                await self._send_error(phone)
                return
            
            # Manejar el estado actual
            try:
                new_state, updated_data = await handler(phone, message, user_data)
                
                # Actualizar estado y datos
                if new_state:
                    conversation_data['state'] = new_state
                    conversation_data['data'] = updated_data
                    await firebase_manager.update_user_state(phone, conversation_data)
                    
            except ValueError as e:
                logger.error(f"Error de validación: {str(e)}")
                await self._send_validation_error(phone, str(e))
                
            except Exception as e:
                logger.error(f"Error procesando mensaje: {str(e)}")
                await self._send_error(phone)
            
        except Exception as e:
            logger.error(f"Error general: {str(e)}")
            await self._send_error(phone)
    
    def _get_state_handler(self, state: str):
        """Obtiene el manejador para un estado específico"""
        handlers = {
            ConversationState.INITIAL.value: self._handle_initial_state,
            ConversationState.ASKING_AREA.value: self._handle_area,
            ConversationState.ASKING_IRRIGATION.value: self._handle_irrigation,
            ConversationState.ASKING_COMMERCIALIZATION.value: self._handle_commercialization,
            ConversationState.ASKING_LOCATION.value: self._handle_location,
            ConversationState.ASKING_LOAN_INTEREST.value: self._handle_loan_interest
        }
        return handlers.get(state)
    
    async def _handle_reset(self, phone: str) -> None:
        """Maneja el comando de reinicio"""
        await firebase_manager.reset_user_state(phone)
        await self.whatsapp.send_message(phone, MESSAGES['welcome'])
    
    async def _handle_initial_state(self, phone: str, message: str, user_data: Dict) -> Tuple[str, Dict]:
        """Maneja el estado inicial (cultivo)"""
        message = normalize_crop(message)
        if not message:
            raise ValueError("Cultivo no reconocido")
        
        # Obtener precio
        try:
            precio = await maga_api.get_precio_cultivo(message)
            user_data['crop'] = message
            user_data['precio'] = precio
            logger.info(f"Precio obtenido para {message}: Q{precio}")
            
            await self.whatsapp.send_message(phone, MESSAGES['ask_area'])
            return ConversationState.ASKING_AREA.value, user_data
            
        except Exception as e:
            logger.error(f"Error obteniendo precio: {str(e)}")
            raise
    
    async def _handle_area(self, phone: str, message: str, user_data: Dict) -> Tuple[str, Dict]:
        """Maneja el ingreso del área"""
        try:
            # Extraer número del mensaje
            import re
            clean_message = message.lower().strip()
            number_match = re.search(r'\d+\.?\d*', clean_message)
            
            if not number_match:
                raise ValueError("Área no válida")
            
            area = float(number_match.group())
            if area <= 0 or area > 1000:
                raise ValueError("Área debe estar entre 0 y 1000 hectáreas")
            
            user_data['area'] = area
            await self.whatsapp.send_message(phone, MESSAGES['ask_irrigation'])
            return ConversationState.ASKING_IRRIGATION.value, user_data
            
        except ValueError as e:
            logger.error(f"Error procesando área: {str(e)} - Input: {message}")
            raise
    
    async def _handle_irrigation(self, phone: str, message: str, user_data: Dict) -> Tuple[str, Dict]:
        """Maneja la selección del sistema de riego"""
        message = normalize_irrigation(message)
        if not message:
            raise ValueError("Sistema de riego no válido")
        
        user_data['irrigation'] = message
        await self.whatsapp.send_message(phone, MESSAGES['ask_commercialization'])
        return ConversationState.ASKING_COMMERCIALIZATION.value, user_data
    
    async def _handle_commercialization(self, phone: str, message: str, user_data: Dict) -> Tuple[str, Dict]:
        """Maneja la selección del método de comercialización"""
        message = normalize_commercialization(message)
        valid_options = {
            'mercado local', 'intermediario', 'exportacion', 'directo'
        }
        
        if message not in valid_options:
            raise ValueError("Método de comercialización no válido")
        
        user_data['commercialization'] = message
        await self.whatsapp.send_message(phone, MESSAGES['ask_location'])
        return ConversationState.ASKING_LOCATION.value, user_data
    
    async def _handle_location(self, phone: str, message: str, user_data: Dict) -> Tuple[str, Dict]:
        """Maneja el ingreso de la ubicación"""
        try:
            user_data['location'] = message
            
            # Calcular análisis financiero
            score = await scoring_service.calculate_score(
                data={
                    'crop': user_data['crop'],
                    'area': float(user_data['area']),
                    'irrigation': user_data['irrigation'],
                    'commercialization': user_data['commercialization']
                },
                precio_actual=user_data['precio']
            )
            
            user_data['score'] = score
            
            # Generar y enviar reporte
            report = report_generator.generate_detailed_report(user_data, score)
            await self.whatsapp.send_message(phone, report)
            
            # Preguntar por préstamo
            await self.whatsapp.send_message(phone, MESSAGES['ask_loan_interest'])
            return ConversationState.ASKING_LOAN_INTEREST.value, user_data
            
        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}")
            raise
    
    async def _handle_loan_interest(self, phone: str, message: str, user_data: Dict) -> Tuple[str, Dict]:
        """Maneja la respuesta sobre interés en el préstamo"""
        message = normalize_yes_no(message)
        
        if message == 'si':
            await self.whatsapp.send_message(phone, MESSAGES['loan_yes'])
            return ConversationState.COMPLETED.value, user_data
        elif message == 'no':
            await self.whatsapp.send_message(phone, MESSAGES['loan_no'])
            return ConversationState.COMPLETED.value, user_data
        else:
            raise ValueError("Respuesta debe ser sí o no")
    
    async def _send_error(self, phone: str) -> None:
        """Envía mensaje de error genérico"""
        await self.whatsapp.send_message(phone, MESSAGES['error'])
    
    async def _send_validation_error(self, phone: str, error: str) -> None:
        """Envía mensaje de error de validación"""
        await self.whatsapp.send_message(phone, MESSAGES['unknown'])

# Instancia global
conversation_manager = ConversationManager()
