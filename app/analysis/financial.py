"""
Módulo para análisis financiero de cultivos
"""
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    """Analizador financiero para proyectos agrícolas"""
    
    # Datos de rendimiento por cultivo (quintales por hectárea)
    RENDIMIENTOS = {
        'maiz': {
            'rendimiento_min': 80,  # qq/ha
            'rendimiento_max': 120,  # qq/ha
            'costos_fijos': {
                'preparacion_tierra': 2000,  # Q/ha
                'sistema_riego': 3000,  # Q/ha
            },
            'costos_variables': {
                'semilla': 800,  # Q/ha
                'fertilizantes': 2500,  # Q/ha
                'pesticidas': 1000,  # Q/ha
                'mano_obra': 3000,  # Q/ha
                'cosecha': 1500,  # Q/ha
            },
            'ciclo_cultivo': 4,  # meses
            'riesgos': 0.2,  # 20% factor de riesgo
        },
        'frijol': {
            'rendimiento_min': 25,
            'rendimiento_max': 35,
            'costos_fijos': {
                'preparacion_tierra': 1800,
                'sistema_riego': 2500,
            },
            'costos_variables': {
                'semilla': 1000,
                'fertilizantes': 2000,
                'pesticidas': 800,
                'mano_obra': 2500,
                'cosecha': 1200,
            },
            'ciclo_cultivo': 3,
            'riesgos': 0.15,
        },
        'papa': {
            'rendimiento_min': 250,
            'rendimiento_max': 350,
            'costos_fijos': {
                'preparacion_tierra': 2500,
                'sistema_riego': 3500,
            },
            'costos_variables': {
                'semilla': 3000,
                'fertilizantes': 3000,
                'pesticidas': 1500,
                'mano_obra': 4000,
                'cosecha': 2000,
            },
            'ciclo_cultivo': 4,
            'riesgos': 0.25,
        }
    }
    
    # Factores de ajuste por método de riego
    FACTOR_RIEGO = {
        'goteo': 1.2,      # 20% más eficiente
        'aspersion': 1.1,  # 10% más eficiente
        'tradicional': 1.0 # base
    }
    
    def __init__(self):
        """Inicializa el analizador"""
        pass
    
    def analizar_proyecto(self, cultivo: str, hectareas: float, 
                         precio_actual: float, metodo_riego: str) -> Dict:
        """
        Realiza un análisis financiero completo del proyecto
        
        Args:
            cultivo: Tipo de cultivo
            hectareas: Número de hectáreas
            precio_actual: Precio actual del cultivo por quintal
            metodo_riego: Método de riego a utilizar
            
        Returns:
            Dict con el análisis financiero completo
        """
        try:
            if cultivo.lower() not in self.RENDIMIENTOS:
                raise ValueError(f"Cultivo {cultivo} no encontrado en la base de datos")
            
            datos_cultivo = self.RENDIMIENTOS[cultivo.lower()]
            factor_riego = self.FACTOR_RIEGO.get(metodo_riego.lower(), 1.0)
            
            # Calcular rendimiento ajustado por riego
            rendimiento_min = datos_cultivo['rendimiento_min'] * factor_riego
            rendimiento_max = datos_cultivo['rendimiento_max'] * factor_riego
            rendimiento_promedio = (rendimiento_min + rendimiento_max) / 2
            
            # Calcular costos totales
            costos_fijos_ha = sum(datos_cultivo['costos_fijos'].values())
            costos_variables_ha = sum(datos_cultivo['costos_variables'].values())
            costos_totales_ha = costos_fijos_ha + costos_variables_ha
            
            costos_totales = costos_totales_ha * hectareas
            
            # Calcular ingresos
            ingresos_min = rendimiento_min * hectareas * precio_actual
            ingresos_max = rendimiento_max * hectareas * precio_actual
            ingresos_promedio = (ingresos_min + ingresos_max) / 2
            
            # Calcular utilidad
            utilidad_min = ingresos_min - costos_totales
            utilidad_max = ingresos_max - costos_totales
            utilidad_promedio = (utilidad_min + utilidad_max) / 2
            
            # Calcular ROI y otros indicadores
            roi_promedio = (utilidad_promedio / costos_totales) * 100
            punto_equilibrio_qq = costos_totales / precio_actual
            
            # Ajustar por factor de riesgo
            utilidad_ajustada = utilidad_promedio * (1 - datos_cultivo['riesgos'])
            
            return {
                'analisis_detallado': {
                    'rendimiento_min_ha': round(rendimiento_min, 2),
                    'rendimiento_max_ha': round(rendimiento_max, 2),
                    'rendimiento_total_min': round(rendimiento_min * hectareas, 2),
                    'rendimiento_total_max': round(rendimiento_max * hectareas, 2),
                    'costos_fijos': round(costos_fijos_ha * hectareas, 2),
                    'costos_variables': round(costos_variables_ha * hectareas, 2),
                    'costos_totales': round(costos_totales, 2),
                    'ingresos_min': round(ingresos_min, 2),
                    'ingresos_max': round(ingresos_max, 2),
                    'utilidad_min': round(utilidad_min, 2),
                    'utilidad_max': round(utilidad_max, 2),
                    'roi': round(roi_promedio, 2),
                    'punto_equilibrio_qq': round(punto_equilibrio_qq, 2),
                    'ciclo_cultivo': datos_cultivo['ciclo_cultivo'],
                    'factor_riesgo': datos_cultivo['riesgos']
                },
                'resumen_financiero': {
                    'inversion_requerida': round(costos_totales, 2),
                    'retorno_esperado': round(utilidad_ajustada, 2),
                    'tiempo_retorno': datos_cultivo['ciclo_cultivo'],
                    'rentabilidad_mensual': round(roi_promedio / datos_cultivo['ciclo_cultivo'], 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis financiero: {str(e)}")
            return None

# Instancia global
financial_analyzer = FinancialAnalyzer()
