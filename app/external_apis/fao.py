"""
Cliente para la API de FAO/FAOSTAT
"""
import httpx
from typing import Dict, Optional
import logging
from datetime import datetime
import json
import os
from ..config import Config

logger = logging.getLogger(__name__)

class FAOClient:
    """Cliente para obtener datos de cultivos de FAO"""
    
    BASE_URL = "https://fenix.fao.org/faostat/api/v1"
    CACHE_DURATION = 24 * 60 * 60  # 24 horas en segundos
    
    def __init__(self):
        """Inicializa el cliente de FAO"""
        self.api_key = os.getenv('FAOSTAT_API_KEY')
        self.session = httpx.AsyncClient(
            headers={
                'X-API-KEY': self.api_key,
                'Accept': 'application/json'
            }
        )
        self._cache = {}
        self._last_update = {}
    
    async def get_crop_data(self, crop_name: str) -> Optional[Dict]:
        """
        Obtiene datos de un cultivo de FAO
        
        Args:
            crop_name: Nombre del cultivo en español
            
        Returns:
            Dict con información del cultivo o None si no se encuentra
        """
        try:
            # Normalizar nombre del cultivo
            crop_name = self._normalize_crop_name(crop_name)
            
            # Verificar cache
            now = datetime.now().timestamp()
            if crop_name in self._cache and \
               now - self._last_update.get(crop_name, 0) < self.CACHE_DURATION:
                return self._cache[crop_name]
            
            # Construir parámetros de consulta
            params = {
                'area': 'GTM',  # Guatemala
                'item': crop_name,
                'element': ['yield', 'production_cost', 'producer_price'],
                'year': '2024',  # Último año disponible
                'format': 'json'
            }
            
            # Hacer request a FAOSTAT
            async with self.session as client:
                response = await client.get(
                    f"{self.BASE_URL}/data",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get('data'):
                    logger.warning(f"No se encontraron datos para {crop_name}")
                    return None
                
                # Procesar datos de FAOSTAT
                processed_data = self._process_faostat_data(data['data'])
                
                # Guardar en cache
                self._cache[crop_name] = processed_data
                self._last_update[crop_name] = now
                
                return processed_data
                
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP obteniendo datos de FAOSTAT: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo datos de cultivo de FAO: {str(e)}")
            return None
    
    def _process_faostat_data(self, raw_data: Dict) -> Dict:
        """
        Procesa datos crudos de FAOSTAT al formato que necesitamos
        """
        try:
            # Extraer datos relevantes
            yield_data = next((item for item in raw_data if item['element'] == 'yield'), {})
            cost_data = next((item for item in raw_data if item['element'] == 'production_cost'), {})
            price_data = next((item for item in raw_data if item['element'] == 'producer_price'), {})
            
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
            
            # Determinar ciclo de cultivo y riesgo basado en el cultivo
            ciclo_cultivo = self._get_crop_cycle(yield_data.get('item'))
            factor_riesgo = self._calculate_risk_factor(
                yield_data.get('item'),
                float(yield_data.get('cv', 20))  # Coeficiente de variación
            )
            
            return {
                'rendimiento_min': rendimiento_min,
                'rendimiento_max': rendimiento_max,
                'costos_fijos': costos_fijos,
                'costos_variables': costos_variables,
                'ciclo_cultivo': ciclo_cultivo,
                'riesgos': factor_riesgo,
                'metadata': {
                    'source': 'FAOSTAT',
                    'last_update': yield_data.get('date_update'),
                    'region': 'Guatemala',
                    'year': yield_data.get('year'),
                    'reliability': yield_data.get('reliability')
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando datos de FAOSTAT: {str(e)}")
            return None
    
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
