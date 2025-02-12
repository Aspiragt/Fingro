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
            price_data = await maga_api.get_precio_cultivo(cultivo)
            
            # Usar el precio del canal especificado o el mejor disponible
            if canal in price_data['precios']:
                precio = price_data['precios'][canal]
            else:
                # Usar el primer canal recomendado
                canal = price_data['canales_recomendados'][0]
                precio = price_data['precios'][canal]
            
            # 2. Calcular costos
            costos = self._get_costos_cultivo(cultivo, area)
            total_costs = sum(costos.values())
            
            # 3. Calcular rendimiento
            rendimiento = self._get_rendimiento_esperado(cultivo, area, riego)
            
            # 4. Calcular ingresos y ganancia
            ingresos = rendimiento * precio
            ganancia = ingresos - total_costs
            
            # 5. Calcular ROI
            roi = (ganancia / total_costs) * 100 if total_costs > 0 else 0
            
            # 6. Calcular riesgo
            risk_score = self._calculate_risk_score(cultivo, canal, riego)
            
            # 7. Calcular score (0-1000)
            score = int((1 - risk_score) * 1000)
            
            # 8. Determinar nivel de riesgo
            if risk_score < 0.3:
                risk_level = "Bajo ✅"
            elif risk_score < 0.6:
                risk_level = "Medio ⚠️"
            else:
                risk_level = "Alto ⛔"
            
            # 9. Calcular préstamo recomendado (80% de costos si riesgo es bajo)
            max_loan = total_costs * (1 - risk_score)
            
            # 10. Calcular cuota mensual (tasa 15% anual, 12 meses)
            tasa_mensual = 0.15 / 12
            cuota = (max_loan * tasa_mensual) / (1 - (1 + tasa_mensual) ** -12)
            
            return {
                'total_costs': total_costs,
                'cost_breakdown': costos,
                'expected_yield': rendimiento,
                'price_info': {
                    'base_price': precio,
                    'adjusted_price': precio,
                    'channel': canal,
                    'recommended_channels': price_data['canales_recomendados']
                },
                'expected_income': ingresos,
                'expected_profit': ganancia,
                'roi': roi,
                'risk_score': risk_score,
                'score': score,
                'risk_level': risk_level,
                'recommended_loan': max_loan,
                'monthly_payment': cuota
            }
            
        except Exception as e:
            logger.error(f"Error en análisis financiero: {str(e)}")
            return None

# Instancia global
financial_model = FinancialModel()
