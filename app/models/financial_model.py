"""
Módulo para análisis financiero de proyectos agrícolas
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging
from app.external_apis.maga import maga_api, CanalComercializacion

logger = logging.getLogger(__name__)

@dataclass
class CostosCultivo:
    """Costos base por hectárea para diferentes cultivos"""
    preparacion_suelo: float
    semilla: float
    fertilizantes: float
    pesticidas: float
    mano_obra: float
    cosecha: float
    otros: float

class FinancialModel:
    """Modelo financiero para proyectos agrícolas"""
    
    def __init__(self):
        """Inicializa el modelo financiero"""
        
        # Costos base por hectárea para diferentes cultivos
        self.costos_cultivos = {
            'maiz': CostosCultivo(
                preparacion_suelo=1200,
                semilla=800,
                fertilizantes=2000,
                pesticidas=1000,
                mano_obra=3000,
                cosecha=1500,
                otros=500
            ),
            'frijol': CostosCultivo(
                preparacion_suelo=1000,
                semilla=1200,
                fertilizantes=1800,
                pesticidas=800,
                mano_obra=2500,
                cosecha=1200,
                otros=500
            ),
            'papa': CostosCultivo(
                preparacion_suelo=1500,
                semilla=3000,
                fertilizantes=2500,
                pesticidas=1500,
                mano_obra=4000,
                cosecha=2000,
                otros=1000
            ),
            'tomate': CostosCultivo(
                preparacion_suelo=2000,
                semilla=4000,
                fertilizantes=3000,
                pesticidas=2000,
                mano_obra=5000,
                cosecha=2500,
                otros=1500
            )
        }
        
        # Factor de rendimiento según sistema de riego
        self.irrigation_yield_factor = {
            'gravedad': 1.0,
            'aspersion': 1.2,
            'goteo': 1.4,
            'ninguno': 0.7
        }
        
        # Rendimiento base por hectárea (quintales)
        self.base_yield = {
            'maiz': 80,
            'frijol': 35,
            'papa': 450,
            'tomate': 800,
            'cafe': 40,
            'chile': 350,
            'cebolla': 600,
            'repollo': 700,
            'arveja': 200,
            'aguacate': 300,
            'platano': 500,
            'limon': 400,
            'zanahoria': 550,
            'brocoli': 400
        }
        
        # Factores de riesgo por canal
        self.risk_factors = {
            CanalComercializacion.EXPORTACION: 0.8,  # Mayor riesgo
            CanalComercializacion.COOPERATIVA: 0.4,
            CanalComercializacion.MAYORISTA: 0.6,
            CanalComercializacion.MERCADO_LOCAL: 0.5
        }
    
    def _get_costos_cultivo(self, cultivo: str, area: float) -> Dict[str, float]:
        """
        Calcula los costos para un cultivo y área específicos
        
        Args:
            cultivo: Nombre del cultivo
            area: Área en hectáreas
            
        Returns:
            Dict[str, float]: Desglose de costos
        """
        # Obtener costos base o usar un cultivo similar
        costos_base = self.costos_cultivos.get(cultivo)
        if not costos_base:
            # Usar costos del maíz como base
            costos_base = self.costos_cultivos['maiz']
            logger.warning(f"Usando costos base de maíz para {cultivo}")
        
        # Calcular costos totales
        return {
            'preparacion_suelo': costos_base.preparacion_suelo * area,
            'semilla': costos_base.semilla * area,
            'fertilizantes': costos_base.fertilizantes * area,
            'pesticidas': costos_base.pesticidas * area,
            'mano_obra': costos_base.mano_obra * area,
            'cosecha': costos_base.cosecha * area,
            'otros': costos_base.otros * area
        }
    
    def _get_rendimiento_esperado(self, cultivo: str, area: float, riego: str) -> float:
        """
        Calcula el rendimiento esperado en quintales
        
        Args:
            cultivo: Nombre del cultivo
            area: Área en hectáreas
            riego: Sistema de riego
            
        Returns:
            float: Rendimiento esperado en quintales
        """
        # Obtener rendimiento base
        base = self.base_yield.get(cultivo, 100)  # 100qq/ha por defecto
        
        # Aplicar factor de riego
        factor = self.irrigation_yield_factor.get(riego, 1.0)
        
        return base * area * factor
    
    def _calculate_risk_score(self, cultivo: str, canal: str, riego: str) -> float:
        """
        Calcula el nivel de riesgo del proyecto
        
        Args:
            cultivo: Nombre del cultivo
            canal: Canal de comercialización
            riego: Sistema de riego
            
        Returns:
            float: Puntaje de riesgo (0-1, donde 1 es más riesgoso)
        """
        # Riesgo base por canal
        risk = self.risk_factors.get(canal, 0.6)
        
        # Ajustar por sistema de riego
        if riego == 'ninguno':
            risk += 0.2
        elif riego in ['goteo', 'aspersion']:
            risk -= 0.1
        
        # Ajustar por tipo de cultivo
        if cultivo in maga_api.export_crops:
            risk += 0.1  # Cultivos de exportación tienen más riesgo
        if cultivo in maga_api.cooperative_crops:
            risk -= 0.1  # Cultivos de cooperativa son más estables
            
        # Mantener el riesgo entre 0 y 1
        return max(0.0, min(1.0, risk))
    
    async def analyze_project(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza un proyecto agrícola y genera reporte financiero
        
        Args:
            user_data: Datos del usuario y proyecto
            
        Returns:
            Dict[str, Any]: Análisis financiero
        """
        try:
            # Extraer datos
            cultivo = user_data['crop'].lower()
            area = float(user_data['area'])
            riego = user_data['irrigation'].lower()
            canal = user_data.get('commercialization', CanalComercializacion.MAYORISTA)
            
            # 1. Obtener precios
            price_data = await maga_api.get_precio_cultivo(cultivo, canal)
            if not price_data or 'precio' not in price_data:
                logger.error(f"Error obteniendo precio para {cultivo}")
                return None
                
            precio_actual = price_data['precio']
            
            # 2. Calcular costos
            costos = self._get_costos_cultivo(cultivo, area)
            costos_totales = sum(costos.values())
            
            # 3. Calcular rendimiento esperado (en quintales)
            rendimiento_total = self._get_rendimiento_esperado(cultivo, area, riego)
            rendimiento_por_hectarea = rendimiento_total / area if area > 0 else 0
            
            # 4. Calcular ingresos
            ingresos_totales = rendimiento_total * precio_actual
            
            # 5. Calcular ganancias
            ganancia_total = ingresos_totales - costos_totales
            ganancia_por_hectarea = ganancia_total / area if area > 0 else 0
            
            # 6. Calcular riesgo
            risk_score = self._calculate_risk_score(cultivo, canal, riego)
            
            return {
                'cultivo': cultivo,
                'area': area,
                'precio_actual': precio_actual,
                'rendimiento_total': rendimiento_total,
                'rendimiento_por_hectarea': rendimiento_por_hectarea,
                'costos_totales': costos_totales,
                'ingresos_totales': ingresos_totales,
                'ganancia_total': ganancia_total,
                'ganancia_por_hectarea': ganancia_por_hectarea,
                'risk_score': risk_score,
                'medida': price_data.get('medida', 'Quintal'),
                'mercado': price_data.get('mercado', 'Nacional')
            }
            
        except Exception as e:
            logger.error(f"Error en análisis financiero: {str(e)}")
            return None

# Instancia global
financial_model = FinancialModel()
