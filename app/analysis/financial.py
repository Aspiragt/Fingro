"""
Módulo para análisis financiero de proyectos agrícolas

Este módulo proporciona herramientas para analizar la viabilidad financiera
de proyectos agrícolas, considerando factores como:
- Rendimiento histórico del cultivo
- Método de riego
- Costos fijos y variables
- Precios actuales del mercado
- Riesgos asociados
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field, validator
from ..external_apis.maga import maga_api

logger = logging.getLogger(__name__)

class ProyectoAgricola(BaseModel):
    """Modelo de datos para un proyecto agrícola"""
    cultivo: str = Field(..., description="Tipo de cultivo a sembrar")
    hectareas: float = Field(..., gt=0, description="Número de hectáreas")
    precio_actual: float = Field(..., gt=0, description="Precio actual por quintal")
    metodo_riego: str = Field(..., description="Método de riego a utilizar")
    
    @validator('metodo_riego')
    def validate_riego(cls, v: str) -> str:
        """Valida que el método de riego sea válido"""
        valid_methods = ['goteo', 'aspersion', 'gravedad', 'temporal']
        v = v.lower().strip()
        if v not in valid_methods:
            raise ValueError(f"Método de riego inválido. Debe ser uno de: {valid_methods}")
        return v
    
    @validator('hectareas')
    def validate_hectareas(cls, v: float) -> float:
        """Valida que el número de hectáreas sea razonable"""
        if v > 1000:
            raise ValueError("El número de hectáreas parece muy alto")
        return v
    
    @validator('precio_actual')
    def validate_precio(cls, v: float) -> float:
        """Valida que el precio sea razonable"""
        if v > 10000:
            raise ValueError("El precio parece muy alto")
        return v

class FinancialAnalyzer:
    """Analizador financiero para proyectos agrícolas"""
    
    # Factores de ajuste por método de riego
    FACTOR_RIEGO = {
        'goteo': 1.2,      # 20% más eficiente
        'aspersion': 1.1,  # 10% más eficiente
        'gravedad': 1.0,   # base
        'temporal': 0.8    # 20% menos eficiente
    }
    
    # Factores de riesgo base por método de riego
    RIESGO_RIEGO = {
        'goteo': 0.1,      # 10% de riesgo
        'aspersion': 0.15, # 15% de riesgo
        'gravedad': 0.2,   # 20% de riesgo
        'temporal': 0.3    # 30% de riesgo
    }
    
    def __init__(self):
        """Inicializa el analizador"""
        pass
    
    async def analizar_proyecto(self, proyecto: ProyectoAgricola) -> Optional[Dict[str, Any]]:
        """
        Realiza un análisis financiero completo del proyecto
        
        Args:
            proyecto: Datos del proyecto agrícola
            
        Returns:
            Optional[Dict[str, Any]]: Análisis financiero o None si hay error
            
        Raises:
            ValueError: Si los datos del proyecto son inválidos
        """
        try:
            logger.info(f"Iniciando análisis para proyecto: {proyecto.dict()}")
            
            # Obtener datos históricos del cultivo
            datos_historicos = await maga_api.get_datos_historicos(proyecto.cultivo)
            if not datos_historicos:
                logger.error(f"No hay datos históricos para: {proyecto.cultivo}")
                return None
            
            # Obtener factor de riego y riesgo
            factor_riego = self.FACTOR_RIEGO[proyecto.metodo_riego]
            factor_riesgo = self.RIESGO_RIEGO[proyecto.metodo_riego]
            
            # Calcular rendimientos
            rendimiento_base = datos_historicos['rendimiento_promedio']
            rendimiento_ajustado = rendimiento_base * factor_riego
            
            # Calcular costos
            costos_fijos = datos_historicos['costos_fijos'] * proyecto.hectareas
            costos_variables = datos_historicos['costos_variables'] * proyecto.hectareas
            costos_totales = costos_fijos + costos_variables
            
            # Calcular ingresos esperados
            ingresos_brutos = rendimiento_ajustado * proyecto.hectareas * proyecto.precio_actual
            
            # Ajustar por riesgos
            riesgo_total = factor_riesgo + datos_historicos.get('riesgo_mercado', 0.1)
            ingresos_ajustados = ingresos_brutos * (1 - riesgo_total)
            
            # Calcular utilidad y ROI
            utilidad_bruta = ingresos_brutos - costos_totales
            utilidad_neta = ingresos_ajustados - costos_totales
            roi = (utilidad_neta / costos_totales) * 100 if costos_totales > 0 else 0
            
            # Calcular punto de equilibrio
            punto_equilibrio = costos_totales / proyecto.precio_actual if proyecto.precio_actual > 0 else 0
            
            # Calcular score
            score = self._calcular_score(
                roi=roi,
                riesgo=riesgo_total,
                hectareas=proyecto.hectareas,
                metodo_riego=proyecto.metodo_riego
            )
            
            logger.info(f"Análisis completado para {proyecto.cultivo}. Score: {score}")
            
            return {
                'resumen': {
                    'score': score,
                    'roi': roi,
                    'utilidad_neta': utilidad_neta,
                    'punto_equilibrio': punto_equilibrio
                },
                'detalle': {
                    'rendimiento': {
                        'base': rendimiento_base,
                        'ajustado': rendimiento_ajustado,
                        'factor_riego': factor_riego
                    },
                    'costos': {
                        'fijos': costos_fijos,
                        'variables': costos_variables,
                        'total': costos_totales
                    },
                    'ingresos': {
                        'brutos': ingresos_brutos,
                        'ajustados': ingresos_ajustados,
                        'factor_riesgo': riesgo_total
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis financiero: {str(e)}")
            return None
    
    def _calcular_score(self, roi: float, riesgo: float, 
                       hectareas: float, metodo_riego: str) -> int:
        """
        Calcula el FinGro Score (0-100) basado en varios factores
        
        Args:
            roi: Return on Investment en porcentaje
            riesgo: Factor de riesgo total (0-1)
            hectareas: Número de hectáreas
            metodo_riego: Método de riego utilizado
            
        Returns:
            int: Score entre 0 y 100
        """
        # Base: ROI (max 40 puntos)
        score_roi = min(40, roi / 2) if roi > 0 else 0
        
        # Riesgo (max 30 puntos)
        score_riesgo = 30 * (1 - riesgo)
        
        # Tecnificación (max 20 puntos)
        score_riego = {
            'goteo': 20,
            'aspersion': 15,
            'gravedad': 10,
            'temporal': 5
        }[metodo_riego]
        
        # Escala (max 10 puntos)
        score_escala = min(10, hectareas / 2)
        
        # Score total
        score_total = int(score_roi + score_riesgo + score_riego + score_escala)
        
        return max(0, min(100, score_total))

# Instancia global
financial_analyzer = FinancialAnalyzer()
