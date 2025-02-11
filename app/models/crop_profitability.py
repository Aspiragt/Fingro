"""
Módulo para calcular rentabilidad de cultivos
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from app.models.crop_yields import calculate_expected_yield
from app.external_apis.maga import maga_client

logger = logging.getLogger(__name__)

async def calculate_crop_profitability(
    crop_name: str,
    area_ha: float,
    efficiency: float = 0.7,
    costs_per_ha: Optional[float] = None  # Costos por hectárea en quetzales
) -> Optional[Dict[str, Any]]:
    """
    Calcula la rentabilidad esperada para un cultivo
    Args:
        crop_name: Nombre del cultivo
        area_ha: Área en hectáreas
        efficiency: Factor de eficiencia (0-1)
        costs_per_ha: Costos por hectárea (opcional)
    Returns:
        Dict con análisis de rentabilidad o None si hay error
    """
    try:
        # Obtener rendimiento esperado
        yield_data = calculate_expected_yield(crop_name, area_ha, efficiency)
        if not yield_data:
            logger.error(f"No se encontraron datos de rendimiento para {crop_name}")
            return None
            
        # Obtener precio actual
        price_data = await maga_client.get_crop_price(crop_name)
        if not price_data:
            logger.error(f"No se encontró precio actual para {crop_name}")
            return None
            
        # Calcular ingresos esperados
        expected_yield_qq = yield_data['expected_yield_qq']
        price_per_qq = price_data['precio']
        expected_revenue = expected_yield_qq * price_per_qq
        
        # Estimar costos si no se proporcionan
        if costs_per_ha is None:
            # Costos estimados como % del ingreso esperado
            estimated_cost_factor = 0.6  # 60% del ingreso
            total_costs = expected_revenue * estimated_cost_factor
        else:
            total_costs = costs_per_ha * area_ha
            
        # Calcular rentabilidad
        profit = expected_revenue - total_costs
        roi = (profit / total_costs) * 100 if total_costs > 0 else 0
        
        return {
            'crop_name': crop_name,
            'analysis_date': datetime.now().isoformat(),
            'area_ha': area_ha,
            'efficiency': efficiency,
            'yield_data': yield_data,
            'price_data': price_data,
            'financial_analysis': {
                'expected_yield_qq': expected_yield_qq,
                'price_per_qq': price_per_qq,
                'expected_revenue': expected_revenue,
                'total_costs': total_costs,
                'expected_profit': profit,
                'roi_percent': roi
            },
            'metadata': {
                'price_source': 'MAGA',
                'price_date': price_data['fecha'],
                'markets': price_data['metadata']['all_markets'],
                'cost_estimation': 'automatic' if costs_per_ha is None else 'manual'
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculando rentabilidad: {str(e)}", exc_info=True)
        return None
