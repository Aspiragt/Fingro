"""
Módulo para análisis financiero de proyectos agrícolas
"""
from typing import Optional, List
from datetime import datetime
import logging
from ..external_apis.fao import fao_client
from ..external_apis.maga import maga_client

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    """Analizador financiero para proyectos agrícolas"""
    
    # Factores de ajuste por método de riego
    FACTOR_RIEGO = {
        'goteo': 1.2,      # 20% más eficiente
        'aspersion': 1.1,  # 10% más eficiente
        'tradicional': 1.0 # base
    }
    
    def __init__(self):
        """Inicializa el analizador"""
        pass
    
    async def analizar_proyecto(self, cultivo: str, hectareas: float, 
                              precio_actual: float, metodo_riego: str) -> dict:
        """
        Realiza un análisis financiero completo del proyecto
        
        Args:
            cultivo: Tipo de cultivo
            hectareas: Número de hectáreas
            precio_actual: Precio actual del cultivo por quintal
            metodo_riego: Método de riego a utilizar
            
        Returns:
            dict con el análisis financiero completo
        """
        try:
            # Obtener datos del cultivo de FAO
            datos_cultivo = await fao_client.get_crop_data(cultivo)
            if not datos_cultivo:
                logger.error(f"No se encontraron datos para el cultivo: {cultivo}")
                return None
            
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
                    'factor_riesgo': datos_cultivo['riesgos'],
                    'metadata': datos_cultivo.get('metadata', {})
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
