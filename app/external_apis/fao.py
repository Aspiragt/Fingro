"""
Cliente para la API de FAOSTAT
"""
import httpx
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import json
import os
from ..config import Config

logger = logging.getLogger(__name__)

class FAOClient:
    """Cliente para obtener datos de cultivos de FAOSTAT"""
    
    BASE_URL = "https://fenixservices.fao.org/faostat/api/v1"
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
        
    def _normalize_crop_name(self, name: str) -> str:
        """Normaliza el nombre del cultivo"""
        name = name.lower().strip()
        # Mapeo de nombres comunes a códigos FAOSTAT
        name_map = {
            'maíz': '56',  # Maize
            'maiz': '56',
            'frijoles': '176',  # Beans, dry
            'fríjol': '176',
            'frijol': '176',
            'frijol negro': '176',
            'tomates': '388',  # Tomatoes
            'tomate': '388',
            'papa': '116',  # Potatoes
            'papas': '116',
            'arroz': '27',  # Rice, paddy
            'café': '656',  # Coffee, green
            'cafe': '656'
        }
        return name_map.get(name, name)
    
    async def get_crop_data(self, crop_name: str) -> Optional[dict]:
        """
        Obtiene datos de un cultivo de FAOSTAT
        
        Args:
            crop_name: Nombre del cultivo en español
            
        Returns:
            dict con información del cultivo o None si no se encuentra
        """
        try:
            # Normalizar nombre del cultivo a código FAOSTAT
            crop_code = self._normalize_crop_name(crop_name)
            if not crop_code.isdigit():
                logger.error(f"Cultivo no soportado: {crop_name}")
                return None
                
            # Verificar cache
            now = datetime.now().timestamp()
            if crop_code in self._cache and \
               now - self._last_update.get(crop_code, 0) < self.CACHE_DURATION:
                return self._cache[crop_code]
            
            # Construir queries para diferentes datos
            production_data = await self._get_production_data(crop_code)
            if not production_data:
                return None
                
            price_data = await self._get_price_data(crop_code)
            if not price_data:
                logger.warning(f"No se encontraron datos de precios para {crop_name}")
                
            # Procesar y combinar datos
            processed_data = self._process_faostat_data(production_data, price_data)
            
            # Guardar en cache
            self._cache[crop_code] = processed_data
            self._last_update[crop_code] = now
            
            return processed_data
                
        except Exception as e:
            logger.error(f"Error obteniendo datos del cultivo {crop_name}: {str(e)}")
            return None
            
    async def _get_production_data(self, crop_code: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de producción de FAOSTAT"""
        try:
            params = {
                'area': 'GTM',  # Guatemala
                'item': crop_code,
                'element': ['5510', '5419'],  # Production, Yield
                'year': '2022',  # Último año disponible
                'show_codes': True,
                'show_unit': True,
                'output_type': 'json'
            }
            
            async with self.session as client:
                response = await client.get(
                    f"{self.BASE_URL}/data/dataset/production",
                    params=params
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error obteniendo datos de producción: {str(e)}")
            return None
            
    async def _get_price_data(self, crop_code: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de precios de FAOSTAT"""
        try:
            params = {
                'area': 'GTM',
                'item': crop_code,
                'element': '5532',  # Producer Price (USD/tonne)
                'year': '2022',
                'show_codes': True,
                'show_unit': True,
                'output_type': 'json'
            }
            
            async with self.session as client:
                response = await client.get(
                    f"{self.BASE_URL}/data/dataset/prices",
                    params=params
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.warning(f"Error obteniendo datos de precios: {str(e)}")
            return None
            
    def _process_faostat_data(self, production_data: Dict[str, Any], 
                             price_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesa datos de FAOSTAT al formato requerido"""
        try:
            # Extraer datos de producción
            yield_value = float(production_data['data'][0]['Value'])
            production_value = float(production_data['data'][1]['Value'])
            
            # Calcular rendimientos
            rendimiento_base = yield_value  # Toneladas por hectárea
            rendimiento_min = rendimiento_base * 0.8
            rendimiento_max = rendimiento_base * 1.2
            
            # Extraer precio si disponible
            price_per_tonne = 0
            if price_data and price_data['data']:
                price_per_tonne = float(price_data['data'][0]['Value'])
            
            # Calcular costos basados en datos históricos y ajustes
            costos_base_ha = 5000  # Costo base por hectárea en USD
            if price_per_tonne > 0:
                costos_base_ha = price_per_tonne * rendimiento_base * 0.6
            
            # Distribuir costos
            costos_fijos = {
                'preparacion_terreno': costos_base_ha * 0.2,
                'sistema_riego': costos_base_ha * 0.3,
                'otros': costos_base_ha * 0.1
            }
            
            costos_variables = {
                'semillas': costos_base_ha * 0.1,
                'fertilizantes': costos_base_ha * 0.15,
                'pesticidas': costos_base_ha * 0.05,
                'mano_obra': costos_base_ha * 0.2,
                'otros': costos_base_ha * 0.1
            }
            
            # Determinar ciclo y riesgo basado en el cultivo
            ciclo_cultivo = self._get_crop_cycle(production_data['data'][0]['ItemCode'])
            factor_riesgo = self._calculate_risk_factor(
                production_data['data'][0]['ItemCode'],
                production_data.get('metadata', {}).get('reliability', 0.2)
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
                    'last_update': production_data.get('metadata', {}).get('lastUpdate'),
                    'region': 'Guatemala',
                    'year': production_data['data'][0]['Year'],
                    'reliability': production_data.get('metadata', {}).get('reliability')
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando datos de FAOSTAT: {str(e)}")
            return None
            
    def _get_crop_cycle(self, crop_code: str) -> int:
        """Determina el ciclo de cultivo en meses"""
        cycles = {
            '56': 4,    # Maíz
            '176': 3,   # Frijol
            '388': 3,   # Tomate
            '116': 4,   # Papa
            '27': 4,    # Arroz
            '656': 12,  # Café
        }
        return cycles.get(str(crop_code), 4)
        
    def _calculate_risk_factor(self, crop_code: str, reliability: float) -> float:
        """Calcula factor de riesgo basado en el cultivo y confiabilidad de datos"""
        # Riesgo base por tipo de cultivo
        crop_risks = {
            '656': 0.1,  # Café (perenne)
            '27': 0.2,   # Arroz
            '56': 0.2,   # Maíz
            '176': 0.25, # Frijol
            '388': 0.3,  # Tomate
            '116': 0.25  # Papa
        }
        
        base_risk = crop_risks.get(str(crop_code), 0.2)
        data_risk = 1 - min(reliability, 0.8)  # Convertir confiabilidad a factor de riesgo
        
        return min(base_risk + data_risk * 0.2, 0.5)  # Cap at 50%

# Cliente global
fao_client = FAOClient()
