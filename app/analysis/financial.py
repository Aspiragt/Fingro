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
        
    def calculate_financial_analysis(self, cultivo: str, area: float, channel: str, irrigation: str) -> Dict[str, Any]:
        """
        Calcula el análisis financiero para un proyecto agrícola
        
        Args:
            cultivo: Tipo de cultivo
            area: Área en hectáreas
            channel: Canal de comercialización 
            irrigation: Sistema de riego
            
        Returns:
            Dict[str, Any]: Análisis financiero
        """
        try:
            # Obtener datos base
            datos_base = maga_api.get_datos_cultivo(cultivo)
            if not datos_base:
                logger.error(f"No hay datos para cultivo: {cultivo}")
                return None
                
            # Obtener factor de riego y riesgo
            factor_riego = self.FACTOR_RIEGO.get(irrigation, 1.0)
            factor_riesgo = self.RIESGO_RIEGO.get(irrigation, 0.3)
            
            # Calculamos rendimiento
            rendimiento_base = datos_base.get('rendimiento_promedio', 30)  # Quintal/hectárea
            rendimiento_ajustado = rendimiento_base * factor_riego
            
            # Calculamos costos
            costo_por_hectarea = datos_base.get('costo_por_hectarea', 8000)
            costos_totales = costo_por_hectarea * area
            
            # Ajustar precio según canal
            precio_base = datos_base.get('precio_quintal', 150)
            factor_precio = {
                'local': 0.9,        # -10% mercado local
                'mayorista': 1.0,    # Precio base
                'cooperativa': 1.1,  # +10% cooperativa
                'exportacion': 1.3   # +30% exportación
            }
            precio_ajustado = precio_base * factor_precio.get(channel, 1.0)
            
            # Calculamos ingresos
            ingresos_brutos = rendimiento_ajustado * area * precio_ajustado
            ingresos_ajustados = ingresos_brutos * (1 - factor_riesgo)
            
            # Calculamos utilidad y ROI
            utilidad_bruta = ingresos_brutos - costos_totales
            utilidad_neta = ingresos_ajustados - costos_totales
            roi = (utilidad_neta / costos_totales) * 100 if costos_totales > 0 else 0
            
            # Calculamos punto de equilibrio
            punto_equilibrio = costos_totales / precio_ajustado if precio_ajustado > 0 else 0
            
            # Calculamos score
            score = self._calcular_score(
                roi=roi,
                riesgo=factor_riesgo,
                hectareas=area,
                metodo_riego=irrigation
            )
            
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
                        'fijos': costos_totales * 0.4,  # Estimación: 40% costos fijos
                        'variables': costos_totales * 0.6,  # Estimación: 60% costos variables
                        'total': costos_totales
                    },
                    'ingresos': {
                        'brutos': ingresos_brutos,
                        'ajustados': ingresos_ajustados,
                        'factor_riesgo': factor_riesgo
                    },
                    'precios': {
                        'precio_actual': precio_ajustado,
                        'precio_por_unidad': precio_ajustado
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
        }.get(metodo_riego.lower(), 5)
        
        # Escala (max 10 puntos)
        score_escala = min(10, hectareas / 2)
        
        # Score total
        score_total = int(score_roi + score_riesgo + score_riego + score_escala)
        
        return max(0, min(100, score_total))
    
    def calculate_loan_amount(self, user_data: Dict[str, Any]) -> float:
        """
        Calcula el monto del préstamo según modelo escalonado basado en hectáreas
        
        Args:
            user_data: Datos del usuario con información del área
            
        Returns:
            float: Monto del préstamo
        """
        area = user_data.get('area', 0)
        
        if area <= 10:
            return 4000
        elif area <= 15:
            return 8000
        else:
            return 16000
    
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
                    },
                    'precios': {
                        'precio_actual': proyecto.precio_actual,
                        'precio_por_unidad': proyecto.precio_actual  # Para compatibilidad con el reporte
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis financiero: {str(e)}")
            return None
    
    def normalize_text(self, text: str) -> str:
        """Normaliza el texto para comparación"""
        import unicodedata
        if not text:
            return ""
        # Normalizar NFD y eliminar diacríticos
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        # A minúsculas y remover espacios extra
        return text.lower().strip()
        
    def parse_department(self, text: str) -> str:
        """
        Parsea y valida un departamento de Guatemala
        
        Args:
            text: Texto a parsear
            
        Returns:
            str: Departamento normalizado o None si no es válido
        """
        text = self.normalize_text(text)
        
        # Mapa de variaciones de departamentos
        departamentos = {
            'guatemala': ['guate', 'ciudad de guatemala', 'ciudad guatemala'],
            'alta verapaz': ['altaverapaz', 'coban', 'cobán'],
            'baja verapaz': ['bajaverapaz', 'salama', 'salamá'],
            'chimaltenango': ['chimal'],
            'chiquimula': [],
            'el progreso': ['progreso', 'guastatoya'],
            'escuintla': [],
            'huehuetenango': ['huehue'],
            'izabal': ['puerto barrios'],
            'jalapa': [],
            'jutiapa': [],
            'petén': ['peten', 'flores'],
            'quetzaltenango': ['xela', 'xelaju', 'xelajú'],
            'quiché': ['quiche', 'el quiché', 'el quiche', 'santa cruz'],
            'retalhuleu': ['reu'],
            'sacatepéquez': ['sacatepequez', 'la antigua', 'antigua'],
            'san marcos': [],
            'santa rosa': ['cuilapa'],
            'sololá': ['solola'],
            'suchitepéquez': ['suchitepequez', 'mazatenango'],
            'totonicapán': ['totonicapan'],
            'zacapa': []
        }
        
        # Buscar coincidencia
        for dept, variations in departamentos.items():
            if text == self.normalize_text(dept) or text in [self.normalize_text(v) for v in variations]:
                return dept.capitalize()
        
        # Si no hay coincidencia exacta, buscar una parcial
        for dept, variations in departamentos.items():
            if self.normalize_text(dept).startswith(text) or any(self.normalize_text(v).startswith(text) for v in variations):
                return dept.capitalize()
                
        return None
    
    def is_crop_suitable(self, crop: str, department: str) -> bool:
        """
        Determina si un cultivo es adecuado para una región
        
        Args:
            crop: Cultivo normalizado
            department: Departamento
            
        Returns:
            bool: True si es adecuado
        """
        # Por ahora, consideramos que todos los cultivos son adecuados
        return True
    
    def calculate_total_costs(self, cultivo: str, area: float, irrigation: str) -> Dict[str, Any]:
        """
        Calcula los costos totales para un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            area: Área en hectáreas
            irrigation: Sistema de riego
            
        Returns:
            Dict con costos desglosados
        """
        datos_cultivo = maga_api.get_datos_cultivo(cultivo)
        costo_base = datos_cultivo.get('costo_por_hectarea', 8000)
        
        # Ajustar por método de riego
        factor_riego = {
            'goteo': 1.2,      # 20% más costoso
            'aspersion': 1.1,  # 10% más costoso
            'gravedad': 1.0,   # base
            'temporal': 0.8    # 20% menos costoso
        }.get(irrigation.lower(), 1.0)
        
        costo_ajustado = costo_base * factor_riego
        costo_total = costo_ajustado * area
        
        return {
            'por_hectarea': costo_ajustado,
            'fijos': costo_total * 0.4,  # 40% costos fijos
            'variables': costo_total * 0.6,  # 60% costos variables
            'total': costo_total
        }
    
    def get_crop_prices(self, cultivo: str, channel: str) -> Dict[str, Any]:
        """
        Obtiene los precios del mercado para un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            channel: Canal de comercialización
            
        Returns:
            Dict con información de precios
        """
        precios = maga_api.get_precio_mercado(cultivo)
        
        # Normalizar canal
        channel = self.normalize_text(channel)
        channel_map = {
            'exportacion': 'exportacion',
            'cooperativa': 'mayorista',  # Usamos mayorista como proxy
            'mayorista': 'mayorista',
            'local': 'local'
        }
        
        canal_normalizado = channel_map.get(channel, 'mayorista')
        precio_actual = precios.get(canal_normalizado, precios.get('mayorista', 150))
        
        return {
            'precio': precio_actual,
            'canal': canal_normalizado,
            'variacion': 0.05  # 5% de variación por defecto
        }
    
    def get_crop_yield(self, cultivo: str, irrigation: str) -> float:
        """
        Obtiene el rendimiento por hectárea para un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            irrigation: Sistema de riego
            
        Returns:
            float: Quintales por hectárea
        """
        datos_cultivo = maga_api.get_datos_cultivo(cultivo)
        rendimiento_base = datos_cultivo.get('rendimiento_promedio', 50)
        
        # Ajustar por método de riego
        factor_riego = self.FACTOR_RIEGO.get(irrigation.lower(), 1.0)
        
        return rendimiento_base * factor_riego
        
# Instancia global
financial_analyzer = FinancialAnalyzer()
