"""
Módulo para calcular el Fingro Score y análisis financiero
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FingroScoring:
    """Calcula el Fingro Score y genera análisis financiero"""
    
    # Pesos para diferentes factores
    WEIGHTS = {
        'area_size': 0.25,          # Tamaño del área
        'irrigation': 0.20,         # Sistema de riego
        'market_access': 0.20,      # Acceso a mercado
        'price_trend': 0.15,        # Tendencia de precios
        'location': 0.20           # Ubicación
    }
    
    # Puntuaciones para sistemas de riego
    IRRIGATION_SCORES = {
        'goteo': 1.0,
        'aspersión': 0.8,
        'gravedad': 0.6,
        'temporal': 0.4
    }
    
    # Puntuaciones para comercialización
    MARKET_SCORES = {
        'exportación': 1.0,
        'mercado local': 0.8,
        'directo': 0.7,
        'intermediario': 0.6
    }
    
    # Costos base por hectárea (en quetzales)
    COSTOS_BASE = {
        'semillas': 1500,
        'fertilizantes': 2000,
        'mano_obra': 3000,
        'riego': {
            'goteo': 5000,
            'aspersión': 4000,
            'gravedad': 2000,
            'temporal': 0
        }
    }
    
    # Factores de ajuste de costos por tipo de comercialización
    FACTOR_COMERCIALIZACION = {
        'exportación': 1.3,  # 30% más caro por estándares de calidad
        'mercado local': 1.0,
        'directo': 0.9,     # 10% más barato por menos intermediarios
        'intermediario': 1.1 # 10% más caro por comisiones
    }
    
    @staticmethod
    def calculate_area_score(hectareas: float) -> float:
        """Calcula score basado en área"""
        if hectareas <= 0:
            return 0
        elif hectareas <= 1:
            return 0.6
        elif hectareas <= 3:
            return 0.8
        elif hectareas <= 10:
            return 1.0
        else:
            return 0.9  # Áreas muy grandes pueden tener más riesgo
    
    @staticmethod
    def calculate_price_trend_score(trend: str) -> float:
        """Calcula score basado en tendencia de precios"""
        trends = {
            'alza': 1.0,
            'estable': 0.8,
            'baja': 0.6
        }
        return trends.get(trend.lower(), 0.7)
    
    @staticmethod
    def calculate_location_score(location: str) -> float:
        """Calcula score basado en ubicación"""
        # TODO: Implementar lógica basada en datos históricos de producción por región
        return 0.8  # Por ahora retorna un valor fijo
    
    @classmethod
    def calculate_score(cls, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula el Fingro Score y genera reporte financiero
        """
        try:
            # Extraer datos
            hectareas = float(user_data.get('hectareas', 0))
            riego = user_data.get('riego', '').lower()
            comercializacion = user_data.get('comercializacion', '').lower()
            ubicacion = user_data.get('ubicacion', '')
            precio_info = user_data.get('precio_info', {})
            tendencia = precio_info.get('tendencia', 'estable').lower()
            
            # Calcular scores individuales
            scores = {
                'area_size': cls.calculate_area_score(hectareas),
                'irrigation': cls.IRRIGATION_SCORES.get(riego, 0.5),
                'market_access': cls.MARKET_SCORES.get(comercializacion, 0.5),
                'price_trend': cls.calculate_price_trend_score(tendencia),
                'location': cls.calculate_location_score(ubicacion)
            }
            
            # Calcular score final
            final_score = sum(score * cls.WEIGHTS[factor] 
                            for factor, score in scores.items())
            
            # Calcular costos
            costo_riego = cls.COSTOS_BASE['riego'].get(riego, 2000)
            costos_base = sum(cost for key, cost in cls.COSTOS_BASE.items() if key != 'riego')
            costos_por_hectarea = costos_base + costo_riego
            
            # Ajustar por comercialización
            factor = cls.FACTOR_COMERCIALIZACION.get(comercializacion, 1.0)
            costos_totales = costos_por_hectarea * hectareas * factor
            
            # Calcular ingresos (estimado conservador)
            precio_promedio = 150  # Precio promedio por quintal
            produccion_por_hectarea = 40  # Quintales por hectárea
            ingreso_total = hectareas * produccion_por_hectarea * precio_promedio
            
            # Calcular ganancia
            ganancia = ingreso_total - costos_totales
            
            # Calcular préstamo recomendado (40% de costos totales)
            prestamo = costos_totales * 0.4
            
            return {
                'fingro_score': round(final_score * 100, 2),
                'prestamo_recomendado': round(prestamo, 2),
                'costos_estimados': round(costos_totales, 2),
                'ingreso_estimado': round(ingreso_total, 2),
                'ganancia_estimada': round(ganancia, 2),
                'scores_detallados': {
                    k: round(v * 100, 2) for k, v in scores.items()
                },
                'fecha_calculo': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando Fingro Score: {str(e)}")
            return None

# Instancia global
scoring = FingroScoring()
