"""
Módulo para calcular el score y análisis financiero
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ScoringService:
    """Servicio para calcular el score y análisis financiero"""
    
    def __init__(self):
        """Inicializa el servicio de scoring"""
        # Factores base por método de comercialización
        self.commercialization_factors = {
            'mercado local': 0.8,    # Menor riesgo pero menor precio
            'intermediario': 0.9,    # Riesgo medio y precio medio
            'exportacion': 1.2,      # Mayor riesgo pero mejor precio
            'directo': 1.1          # Riesgo bajo y buen precio
        }
        
        # Factores por sistema de riego
        self.irrigation_factors = {
            'goteo': 1.2,      # Mejor eficiencia y control
            'aspersion': 1.1,  # Buena eficiencia
            'gravedad': 0.9,   # Menor eficiencia
            'temporal': 0.8    # Mayor riesgo
        }
        
        # Costos base por hectárea (Q/ha)
        self.base_costs = {
            'maiz': 8000,
            'frijol': 6000,
            'cafe': 15000,
            'tomate': 25000,
            'chile': 20000,
            'papa': 18000,
            'cebolla': 16000,
            'repollo': 12000,
            'arveja': 10000
        }
        
        # Rendimientos promedio por hectárea (quintales/ha)
        self.yield_per_ha = {
            'maiz': 80,
            'frijol': 25,
            'cafe': 40,
            'tomate': 800,
            'chile': 400,
            'papa': 350,
            'cebolla': 400,
            'repollo': 500,
            'arveja': 100
        }
    
    async def calculate_score(self, data: Dict[str, Any], precio_actual: float) -> Dict[str, Any]:
        """
        Calcula el score y análisis financiero
        
        Args:
            data: Diccionario con datos del proyecto
            precio_actual: Precio actual del cultivo
            
        Returns:
            Dict con el análisis completo
        """
        try:
            # Extraer datos
            crop = data['crop']
            area = float(data['area'])
            irrigation = data['irrigation']
            commercialization = data['commercialization']
            
            # Validar datos
            if crop not in self.base_costs:
                raise ValueError(f"Cultivo no soportado: {crop}")
            if area <= 0:
                raise ValueError("Área debe ser mayor a 0")
            if irrigation not in self.irrigation_factors:
                raise ValueError(f"Sistema de riego no válido: {irrigation}")
            if commercialization not in self.commercialization_factors:
                raise ValueError(f"Método de comercialización no válido: {commercialization}")
            
            # Calcular costos
            base_cost = self.base_costs[crop]
            total_cost = base_cost * area
            
            # Ajustar por sistema de riego
            irrigation_factor = self.irrigation_factors[irrigation]
            total_cost *= irrigation_factor
            
            # Calcular producción esperada
            base_yield = self.yield_per_ha[crop]
            expected_yield = base_yield * area * irrigation_factor
            
            # Calcular ingresos
            price_factor = self.commercialization_factors[commercialization]
            adjusted_price = precio_actual * price_factor
            expected_income = expected_yield * adjusted_price
            
            # Calcular ganancia
            expected_profit = expected_income - total_cost
            
            # Calcular ROI
            roi = (expected_profit / total_cost) * 100
            
            # Calcular score base (0-1000)
            base_score = 500
            
            # Ajustar por ROI
            if roi >= 100:
                base_score += 200
            elif roi >= 50:
                base_score += 100
            elif roi >= 25:
                base_score += 50
            
            # Ajustar por sistema de riego
            if irrigation == 'goteo':
                base_score += 100
            elif irrigation == 'aspersion':
                base_score += 75
            elif irrigation == 'gravedad':
                base_score += 50
            
            # Ajustar por método de comercialización
            if commercialization == 'exportacion':
                base_score += 100
            elif commercialization == 'directo':
                base_score += 75
            elif commercialization == 'intermediario':
                base_score += 50
            
            # Ajustar por área
            if area >= 5:
                base_score += 100
            elif area >= 2:
                base_score += 50
            elif area >= 1:
                base_score += 25
            
            # Normalizar score
            final_score = min(1000, max(300, base_score))
            
            # Calcular préstamo recomendado (75% de costos)
            recommended_loan = total_cost * 0.75
            
            # Preparar respuesta
            return {
                'score': final_score,
                'risk_level': self._get_risk_level(final_score),
                'total_costs': total_cost,
                'expected_yield': expected_yield,
                'expected_income': expected_income,
                'expected_profit': expected_profit,
                'roi': roi,
                'recommended_loan': recommended_loan,
                'monthly_payment': self._calculate_monthly_payment(recommended_loan),
                'price_info': {
                    'base_price': precio_actual,
                    'adjusted_price': adjusted_price,
                    'unit': 'quintal'
                },
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en calculate_score: {str(e)}")
            raise
    
    def _get_risk_level(self, score: float) -> str:
        """Determina el nivel de riesgo basado en el score"""
        if score >= 800:
            return "Bajo"
        elif score >= 650:
            return "Medio-Bajo"
        elif score >= 500:
            return "Medio"
        else:
            return "Alto"
    
    def _calculate_monthly_payment(self, loan_amount: float, annual_rate: float = 15, months: int = 12) -> float:
        """
        Calcula el pago mensual del préstamo
        
        Args:
            loan_amount: Monto del préstamo
            annual_rate: Tasa anual (default: 15%)
            months: Plazo en meses (default: 12)
            
        Returns:
            float: Pago mensual
        """
        # Convertir tasa anual a mensual
        monthly_rate = (annual_rate / 100) / 12
        
        # Calcular pago mensual usando fórmula de amortización
        payment = loan_amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
        
        return payment

# Instancia global
scoring_service = ScoringService()
