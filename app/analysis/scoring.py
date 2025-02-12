"""
Módulo para calcular el Fingro Score y análisis financiero
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ScoringService:
    """Calcula el Fingro Score y genera análisis financiero"""
    
    # Costos base por hectárea (en quetzales)
    COSTOS_BASE = {
        'preparacion_tierra': 2000,  # Preparación de tierra
        'semillas': 1500,           # Semillas/plantas
        'fertilizantes': 2000,      # Fertilizantes básicos
        'mano_obra': 3000,          # Mano de obra básica
        'otros': 1000               # Otros gastos básicos
    }
    
    # Costos de riego por hectárea
    COSTOS_RIEGO = {
        'goteo': 5000,      # Sistema completo de goteo
        'aspersion': 4000,  # Sistema de aspersión
        'gravedad': 2000,   # Sistema por gravedad
        'temporal': 0       # Sin sistema de riego
    }
    
    # Factores de ajuste por tipo de comercialización
    FACTOR_COMERCIALIZACION = {
        'exportacion': 1.3,     # 30% más caro por estándares de calidad
        'mercado local': 1.0,   # Precio base del mercado
        'directo': 0.9,         # 10% más barato por menos intermediarios
        'intermediario': 1.1    # 10% más caro por comisiones
    }
    
    # Puntajes base por tipo de riego
    SCORE_RIEGO = {
        'goteo': 100,      # Máxima eficiencia
        'aspersion': 80,   # Alta eficiencia
        'gravedad': 60,    # Eficiencia media
        'temporal': 40     # Baja eficiencia
    }
    
    # Puntajes base por tipo de comercialización
    SCORE_COMERCIALIZACION = {
        'exportacion': 100,     # Mejor mercado
        'mercado local': 80,    # Buen mercado
        'directo': 70,          # Mercado limitado
        'intermediario': 60     # Menor control
    }
    
    async def calculate_score(self, data: Dict[str, Any], precio_actual: Optional[float] = None) -> Dict[str, Any]:
        """
        Calcula el Fingro Score y genera análisis financiero
        
        Args:
            data: Datos del proyecto
            precio_actual: Precio actual del cultivo (opcional)
            
        Returns:
            Dict[str, Any]: Resultados del análisis
        """
        try:
            # Validar datos requeridos
            required_fields = ['crop', 'area', 'irrigation', 'commercialization']
            if not all(field in data for field in required_fields):
                raise ValueError("Faltan datos requeridos para el análisis")
            
            # Calcular costos
            costos_base = sum(self.COSTOS_BASE.values()) * data['area']
            costos_riego = self.COSTOS_RIEGO.get(data['irrigation'], 0) * data['area']
            factor_comercializacion = self._calcular_factor_comercializacion(data['commercialization'])
            
            costos_totales = (costos_base + costos_riego) * factor_comercializacion
            
            # Calcular ingresos estimados
            precio_venta = precio_actual if precio_actual else 150  # Precio por defecto
            rendimiento_estimado = self._estimar_rendimiento(data['irrigation'])
            ingresos_estimados = precio_venta * rendimiento_estimado * data['area']
            
            # Calcular ganancia estimada
            ganancia_estimada = ingresos_estimados - costos_totales
            
            # Calcular Fingro Score
            score_riego = self.SCORE_RIEGO.get(data['irrigation'], 0)
            score_comercializacion = self._calcular_score_comercializacion(data['commercialization'])
            
            # Ajustar score por área
            score_area = min(100, data['area'] * 10)  # 10 puntos por hectárea, máximo 100
            
            # Ajustar score por rentabilidad
            rentabilidad = (ganancia_estimada / costos_totales) * 100
            score_rentabilidad = min(100, max(0, rentabilidad))
            
            # Calcular score final (promedio ponderado)
            fingro_score = int((
                score_riego * 0.3 +           # 30% peso
                score_comercializacion * 0.3 + # 30% peso
                score_area * 0.2 +            # 20% peso
                score_rentabilidad * 0.2       # 20% peso
            ))
            
            # Calcular préstamo recomendado (hasta 80% de costos totales)
            prestamo_maximo = costos_totales * 0.8
            prestamo_recomendado = (prestamo_maximo * fingro_score) / 100
            
            return {
                'fingro_score': fingro_score,
                'costos_estimados': costos_totales,
                'ingreso_estimado': ingresos_estimados,
                'ganancia_estimada': ganancia_estimada,
                'prestamo_recomendado': prestamo_recomendado,
                'detalles': {
                    'score_riego': score_riego,
                    'score_comercializacion': score_comercializacion,
                    'score_area': score_area,
                    'score_rentabilidad': score_rentabilidad,
                    'rentabilidad': rentabilidad
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculando Fingro Score: {str(e)}")
            raise
    
    def _calcular_factor_comercializacion(self, comercializacion: str) -> float:
        """
        Calcula el factor de ajuste por tipo de comercialización
        
        Args:
            comercializacion: Método de comercialización
        
        Returns:
            float: Factor de ajuste
        """
        return self.FACTOR_COMERCIALIZACION.get(comercializacion.lower().strip(), 1.0)
    
    def _calcular_score_comercializacion(self, comercializacion: str) -> float:
        """
        Calcula el score basado en el método de comercialización
        
        Args:
            comercializacion: Método de comercialización
        
        Returns:
            float: Score entre 0 y 1
        """
        return self.SCORE_COMERCIALIZACION.get(comercializacion.lower().strip(), 60) / 100.0
    
    def _estimar_rendimiento(self, tipo_riego: str) -> float:
        """
        Estima el rendimiento por hectárea según el tipo de riego
        
        Args:
            tipo_riego: Tipo de sistema de riego
            
        Returns:
            float: Rendimiento estimado en quintales por hectárea
        """
        rendimientos = {
            'goteo': 50,      # Máximo rendimiento
            'aspersion': 40,  # Alto rendimiento
            'gravedad': 30,   # Rendimiento medio
            'temporal': 20    # Bajo rendimiento
        }
        return rendimientos.get(tipo_riego, 30)  # Por defecto, rendimiento medio

# Instancia global
scoring_service = ScoringService()
