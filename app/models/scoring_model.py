from typing import Dict, Optional
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class FingroScore:
    def __init__(self):
        self.base_score = 500
        self.max_score = 1000
        
    def calculate_score(self, user_data: Dict) -> Dict:
        """
        Calcula el Fingro Score basado en múltiples factores
        """
        score = self.base_score
        
        # Factor 1: Uso de WhatsApp para negocios
        if user_data.get('uses_whatsapp_business', False):
            score += 150
            
        # Factor 2: Historial de transacciones digitales
        if user_data.get('digital_transactions_count', 0) > 0:
            score += min(200, user_data['digital_transactions_count'] * 20)
            
        # Factor 3: Consistencia en cultivos
        if user_data.get('farming_years', 0) > 2:
            score += min(100, user_data['farming_years'] * 10)
            
        # Factor 4: Red de contactos comerciales
        business_contacts = user_data.get('business_contacts_count', 0)
        score += min(100, business_contacts * 5)
        
        # Normalizar score
        final_score = min(self.max_score, max(300, score))
        
        return {
            'score': final_score,
            'risk_level': self._get_risk_level(final_score),
            'max_credit_amount': self._calculate_max_credit(final_score),
            'interest_rate': self._calculate_interest_rate(final_score)
        }
    
    def _get_risk_level(self, score: float) -> str:
        if score >= 800:
            return "Bajo"
        elif score >= 650:
            return "Medio-Bajo"
        elif score >= 500:
            return "Medio"
        else:
            return "Alto"
    
    def _calculate_max_credit(self, score: float) -> float:
        """
        Calcula el monto máximo de crédito basado en el score
        """
        base_amount = 1000  # USD
        multiplier = (score / 500) ** 2
        return round(base_amount * multiplier, 2)
    
    def _calculate_interest_rate(self, score: float) -> float:
        """
        Calcula la tasa de interés basada en el score
        """
        base_rate = 0.35  # 35% anual
        score_discount = (score - 500) / 1000  # Descuento basado en score
        final_rate = base_rate - (score_discount * 0.20)  # Máximo descuento de 20%
        return round(max(0.15, final_rate), 4)  # Mínimo 15% anual

class WhatsAppFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Extrae características relevantes de la interacción por WhatsApp
    """
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        features = []
        for conversation in X:
            features.append({
                'response_time_avg': self._calculate_avg_response_time(conversation),
                'message_length_avg': self._calculate_avg_message_length(conversation),
                'business_related_msgs': self._count_business_messages(conversation),
                'completion_rate': self._calculate_completion_rate(conversation)
            })
        return np.array(features)
    
    def _calculate_avg_response_time(self, conversation: Dict) -> float:
        # Implementar lógica de cálculo de tiempo de respuesta promedio
        pass
    
    def _calculate_avg_message_length(self, conversation: Dict) -> float:
        # Implementar lógica de cálculo de longitud promedio de mensajes
        pass
    
    def _count_business_messages(self, conversation: Dict) -> int:
        # Implementar lógica de conteo de mensajes relacionados con negocios
        pass
    
    def _calculate_completion_rate(self, conversation: Dict) -> float:
        # Implementar lógica de cálculo de tasa de completitud de la conversación
        pass
