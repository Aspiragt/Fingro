"""
Módulo para manejar datos de rendimiento de cultivos
Fuentes:
- MAGA
- FAO
- IICA
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CropYield:
    """Datos de rendimiento de un cultivo"""
    crop_name: str  # Nombre del cultivo
    yield_per_ha: float  # Rendimiento en quintales por hectárea
    growing_time: int  # Tiempo de cultivo en días
    water_requirements: float  # Requerimiento de agua en mm/ciclo
    optimal_altitude: tuple[int, int]  # Rango de altura óptima en metros
    optimal_temp: tuple[float, float]  # Rango de temperatura óptima en °C
    source: str  # Fuente de los datos
    last_update: datetime  # Última actualización

# Datos de rendimiento por cultivo
# Fuente: MAGA, FAO, IICA
CROP_YIELDS = {
    'tomate': CropYield(
        crop_name='tomate',
        yield_per_ha=2000.0,  # ~2000 quintales/ha en condiciones óptimas
        growing_time=90,  # 90-120 días
        water_requirements=600.0,  # 600-800mm/ciclo
        optimal_altitude=(0, 2000),  # 0-2000m
        optimal_temp=(18.0, 25.0),  # 18-25°C
        source='MAGA',
        last_update=datetime(2025, 1, 1)
    ),
    'papa': CropYield(
        crop_name='papa',
        yield_per_ha=400.0,  # ~400 quintales/ha
        growing_time=120,  # 120-150 días
        water_requirements=500.0,  # 500-700mm/ciclo
        optimal_altitude=(1500, 3000),  # 1500-3000m
        optimal_temp=(15.0, 20.0),  # 15-20°C
        source='MAGA',
        last_update=datetime(2025, 1, 1)
    ),
    'maiz': CropYield(
        crop_name='maiz',
        yield_per_ha=80.0,  # ~80 quintales/ha
        growing_time=120,  # 120-150 días
        water_requirements=500.0,  # 500-800mm/ciclo
        optimal_altitude=(0, 2000),  # 0-2000m
        optimal_temp=(20.0, 30.0),  # 20-30°C
        source='MAGA',
        last_update=datetime(2025, 1, 1)
    ),
    'frijol': CropYield(
        crop_name='frijol',
        yield_per_ha=30.0,  # ~30 quintales/ha
        growing_time=90,  # 90-120 días
        water_requirements=300.0,  # 300-500mm/ciclo
        optimal_altitude=(400, 1200),  # 400-1200m
        optimal_temp=(15.0, 27.0),  # 15-27°C
        source='MAGA',
        last_update=datetime(2025, 1, 1)
    ),
}

def get_crop_yield(crop_name: str) -> Optional[CropYield]:
    """
    Obtiene datos de rendimiento de un cultivo
    Args:
        crop_name: Nombre del cultivo
    Returns:
        CropYield con datos del cultivo o None si no existe
    """
    return CROP_YIELDS.get(crop_name.lower())

def calculate_expected_yield(
    crop_name: str,
    area_ha: float,
    efficiency: float = 0.7  # Factor de eficiencia (0-1)
) -> Optional[Dict[str, Any]]:
    """
    Calcula el rendimiento esperado para un área y cultivo
    Args:
        crop_name: Nombre del cultivo
        area_ha: Área en hectáreas
        efficiency: Factor de eficiencia (0-1)
    Returns:
        Dict con datos de rendimiento o None si hay error
    """
    crop_yield = get_crop_yield(crop_name)
    if not crop_yield:
        return None
        
    # Calcular rendimiento esperado
    expected_yield = crop_yield.yield_per_ha * area_ha * efficiency
    
    return {
        'crop_name': crop_name,
        'area_ha': area_ha,
        'efficiency': efficiency,
        'yield_data': crop_yield,
        'expected_yield_qq': expected_yield,
        'growing_time_days': crop_yield.growing_time,
        'water_requirements_mm': crop_yield.water_requirements,
    }
