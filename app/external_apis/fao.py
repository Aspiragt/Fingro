"""
Cliente para la API de FAODATA Explorer
"""
import httpx
from typing import Optional
import logging
from datetime import datetime
import json
import os
from ..config import Config

logger = logging.getLogger(__name__)

class FAOClient:
    """Cliente para obtener datos de cultivos de FAO"""
    
    BASE_URL = "https://dataexplorer.fao.org/api/v1"
    CACHE_DURATION = 24 * 60 * 60  # 24 horas en segundos
    
    def __init__(self):
        """Inicializa el cliente de FAO"""
        self.session = httpx.AsyncClient(
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        self._cache = {}
        self._last_update = {}
    
    async def get_crop_data(self, crop_name: str) -> Optional[dict]:
        """
        Obtiene datos de un cultivo de FAO
        
        Args:
            crop_name: Nombre del cultivo en español
            
        Returns:
            dict con información del cultivo o None si no se encuentra
        """
        try:
            # Normalizar nombre del cultivo
            crop_name = self._normalize_crop_name(crop_name)
            
            # Verificar cache
            now = datetime.now().timestamp()
            if crop_name in self._cache and \
               now - self._last_update.get(crop_name, 0) < self.CACHE_DURATION:
                return self._cache[crop_name]
            
            # Construir query para FAODATA
            query = {
                "query": [
                    {
                        "dimension": "area",
                        "codes": ["GTM"]  # Guatemala
                    },
                    {
                        "dimension": "item",
                        "codes": [crop_name]
                    },
                    {
                        "dimension": "element",
                        "codes": ["5419", "5510", "5312"]  # Yield, Producer Price, Production Cost
                    },
                    {
                        "dimension": "year",
                        "codes": ["2024"]
                    }
                ],
                "format": "json",
                "language": "en"
            }
            
            # Hacer request a FAODATA
            async with self.session as client:
                response = await client.post(
                    f"{self.BASE_URL}/data/query",
                    json=query
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get('data'):
                    logger.warning(f"No se encontraron datos para {crop_name}")
                    # Usar datos de respaldo si no hay datos en FAODATA
                    backup_data = self._get_backup_data(crop_name)
                    if backup_data:
                        self._cache[crop_name] = backup_data
                        self._last_update[crop_name] = now
                        return backup_data
                    return None
                
                # Procesar datos de FAODATA
                processed_data = self._process_faodata(data['data'])
                
                # Guardar en cache
                self._cache[crop_name] = processed_data
                self._last_update[crop_name] = now
                
                return processed_data
                
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP obteniendo datos de FAODATA: {str(e)}")
            return self._get_backup_data(crop_name)
        except Exception as e:
            logger.error(f"Error obteniendo datos de cultivo de FAO: {str(e)}")
            return self._get_backup_data(crop_name)
    
    def _process_faodata(self, raw_data: dict) -> dict:
        """
        Procesa datos crudos de FAODATA al formato que necesitamos
        """
        try:
            # Extraer datos relevantes
            yield_data = next((item for item in raw_data if item.get('element_code') == '5419'), {})
            price_data = next((item for item in raw_data if item.get('element_code') == '5510'), {})
            cost_data = next((item for item in raw_data if item.get('element_code') == '5312'), {})
            
            # Calcular rendimientos
            base_yield = float(yield_data.get('value', 0))
            rendimiento_min = base_yield * 0.8  # 20% menos del promedio
            rendimiento_max = base_yield * 1.2  # 20% más del promedio
            
            # Calcular costos
            base_cost = float(cost_data.get('value', 0))
            costos_fijos = {
                'preparacion_tierra': base_cost * 0.2,
                'sistema_riego': base_cost * 0.3,
            }
            costos_variables = {
                'semilla': base_cost * 0.1,
                'fertilizantes': base_cost * 0.15,
                'pesticidas': base_cost * 0.1,
                'mano_obra': base_cost * 0.1,
                'cosecha': base_cost * 0.05,
            }
            
            # Determinar ciclo de cultivo y riesgo
            ciclo_cultivo = self._get_crop_cycle(yield_data.get('item_code'))
            factor_riesgo = self._calculate_risk_factor(
                yield_data.get('item_code'),
                float(yield_data.get('cv', 20))
            )
            
            return {
                'rendimiento_min': rendimiento_min,
                'rendimiento_max': rendimiento_max,
                'costos_fijos': costos_fijos,
                'costos_variables': costos_variables,
                'ciclo_cultivo': ciclo_cultivo,
                'riesgos': factor_riesgo,
                'metadata': {
                    'source': 'FAODATA',
                    'last_update': yield_data.get('date_update'),
                    'region': 'Guatemala',
                    'year': yield_data.get('year'),
                    'reliability': yield_data.get('flag_description')
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando datos de FAODATA: {str(e)}")
            return None
    
    def _get_backup_data(self, crop_name: str) -> Optional[dict]:
        """
        Datos de respaldo cuando la API falla o no tiene datos
        Basado en promedios históricos de Guatemala
        """
        backup_data = {
            'maize': {
                'rendimiento_min': 80,
                'rendimiento_max': 120,
                'costos_fijos': {
                    'preparacion_tierra': 2000,
                    'sistema_riego': 3000,
                },
                'costos_variables': {
                    'semilla': 800,
                    'fertilizantes': 2500,
                    'pesticidas': 1000,
                    'mano_obra': 3000,
                    'cosecha': 1500,
                },
                'ciclo_cultivo': 4,
                'riesgos': 0.2,
                'metadata': {
                    'source': 'Historical Data',
                    'last_update': '2024-12-31',
                    'region': 'Guatemala',
                    'reliability': 'Estimated'
                }
            },
            'beans': {
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
                'metadata': {
                    'source': 'Historical Data',
                    'last_update': '2024-12-31',
                    'region': 'Guatemala',
                    'reliability': 'Estimated'
                }
            }
        }
        return backup_data.get(crop_name)
    
    def _get_crop_cycle(self, crop_code: str) -> int:
        """Determina el ciclo de cultivo en meses"""
        cycles = {
            'maize': 4,
            'beans': 3,
            'potato': 4,
            'tomato': 3,
            'onion': 3,
            'carrot': 3,
            'chili': 4,
            'coffee': 12,
            'rice': 4,
            'wheat': 4
        }
        return cycles.get(crop_code, 4)  # 4 meses por defecto
    
    def _calculate_risk_factor(self, crop_code: str, cv: float) -> float:
        """
        Calcula factor de riesgo basado en el cultivo y su coeficiente de variación
        """
        # Base risk from coefficient of variation (normalized)
        base_risk = min(cv / 100, 0.5)  # Cap at 50%
        
        # Additional risk factors by crop type
        crop_risks = {
            'coffee': 0.1,  # Cultivos perennes, menor riesgo
            'banana': 0.1,
            'rice': 0.2,    # Cultivos básicos, riesgo medio
            'maize': 0.2,
            'beans': 0.25,  # Cultivos sensibles, mayor riesgo
            'tomato': 0.3,
            'potato': 0.25
        }
        
        additional_risk = crop_risks.get(crop_code, 0.2)
        return min(base_risk + additional_risk, 0.8)  # Cap total risk at 80%
    
    def _normalize_crop_name(self, name: str) -> str:
        """Normaliza el nombre del cultivo para búsqueda"""
        translations = {
            'maiz': 'maize',
            'frijol': 'beans',
            'papa': 'potato',
            'tomate': 'tomato',
            'cebolla': 'onion',
            'zanahoria': 'carrot',
            'chile': 'chili',
            'cafe': 'coffee',
            'arroz': 'rice',
            'trigo': 'wheat'
        }
        return translations.get(name.lower(), name.lower())

# Cliente global
fao_client = FAOClient()
