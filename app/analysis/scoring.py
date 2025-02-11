"""
Módulo para calcular el Fingro Score y análisis financiero
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FingroScoring:
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
        'aspersión': 4000,  # Sistema de aspersión
        'gravedad': 2000,   # Sistema por gravedad
        'temporal': 0       # Sin sistema de riego
    }
    
    # Factores de ajuste por tipo de comercialización
    FACTOR_COMERCIALIZACION = {
        'exportación': 1.3,  # 30% más caro por estándares de calidad
        'mercado local': 1.0,
        'directo': 0.9,     # 10% más barato por menos intermediarios
        'intermediario': 1.1 # 10% más caro por comisiones
    }
    
    # Datos de producción por defecto (por hectárea)
    DATOS_PRODUCCION = {
        'produccion_baja': {
            'quintales': 30,
            'precio_promedio': 120
        },
        'produccion_media': {
            'quintales': 40,
            'precio_promedio': 150
        },
        'produccion_alta': {
            'quintales': 50,
            'precio_promedio': 180
        }
    }
    
    def calculate_score(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula el Fingro Score y genera reporte financiero
        """
        try:
            # Extraer datos
            hectareas = float(user_data.get('hectareas', 0))
            riego = user_data.get('riego', '').lower()
            comercializacion = user_data.get('comercializacion', '').lower()
            
            # 1. Calcular costos base
            costos_base = sum(self.COSTOS_BASE.values())
            costo_riego = self.COSTOS_RIEGO.get(riego, self.COSTOS_RIEGO['temporal'])
            costos_por_hectarea = costos_base + costo_riego
            
            # 2. Ajustar por comercialización
            factor = self.FACTOR_COMERCIALIZACION.get(comercializacion, 1.0)
            costos_totales = costos_por_hectarea * hectareas * factor
            
            # 3. Calcular producción estimada (usando escenario medio por defecto)
            datos_prod = self.DATOS_PRODUCCION['produccion_media']
            quintales_por_hectarea = datos_prod['quintales']
            precio_promedio = datos_prod['precio_promedio']
            
            # 4. Calcular ingresos
            produccion_total = hectareas * quintales_por_hectarea
            ingreso_total = produccion_total * precio_promedio
            
            # 5. Calcular ganancia
            ganancia = ingreso_total - costos_totales
            
            # 6. Calcular Fingro Score (0-100)
            score_base = 60  # Puntaje base
            
            # Ajustes al score
            if ganancia > 0:
                score_base += min(20, int(ganancia / costos_totales * 100))  # Hasta 20 puntos por rentabilidad
            
            if hectareas >= 1:
                score_base += min(10, int(hectareas * 2))  # Hasta 10 puntos por escala
                
            if riego in ['goteo', 'aspersión']:
                score_base += 10  # 10 puntos por tecnificación
                
            if comercializacion in ['exportación', 'directo']:
                score_base += 5   # 5 puntos por canal de venta optimizado
            
            # Limitar score entre 0 y 100
            fingro_score = max(0, min(100, score_base))
            
            # 7. Calcular préstamo recomendado (basado en costos y score)
            factor_prestamo = fingro_score / 100  # Factor de riesgo basado en score
            prestamo_base = costos_totales * 0.6  # Hasta 60% de los costos totales
            prestamo_recomendado = prestamo_base * factor_prestamo
            
            # 8. Limitar el préstamo entre Q5,000 y Q100,000
            prestamo_recomendado = max(5000, min(100000, prestamo_recomendado))
            
            return {
                'fingro_score': fingro_score,
                'prestamo_recomendado': round(prestamo_recomendado, 2),
                'costos_estimados': round(costos_totales, 2),
                'ingreso_estimado': round(ingreso_total, 2),
                'ganancia_estimada': round(ganancia, 2),
                'detalle_costos': {
                    'preparacion_tierra': self.COSTOS_BASE['preparacion_tierra'] * hectareas,
                    'semillas': self.COSTOS_BASE['semillas'] * hectareas,
                    'fertilizantes': self.COSTOS_BASE['fertilizantes'] * hectareas,
                    'mano_obra': self.COSTOS_BASE['mano_obra'] * hectareas,
                    'riego': costo_riego * hectareas,
                    'otros': self.COSTOS_BASE['otros'] * hectareas
                },
                'produccion_estimada': {
                    'quintales_por_hectarea': quintales_por_hectarea,
                    'quintales_totales': produccion_total,
                    'precio_promedio': precio_promedio
                },
                'fecha_calculo': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando Fingro Score: {str(e)}")
            return None

# Instancia global
scoring = FingroScoring()
