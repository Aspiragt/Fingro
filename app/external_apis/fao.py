"""
Cliente para la API de FAOSTAT (Food and Agriculture Organization of the United Nations)
https://www.fao.org/faostat/en/#data/
"""
import httpx
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
import json
import pandas as pd
from difflib import get_close_matches

logger = logging.getLogger(__name__)

class FAOClient:
    """Cliente para obtener datos de precios de FAOSTAT"""
    
    BASE_URL = "https://data.apps.fao.org/api/v1"
    CACHE_DURATION = 1 * 60 * 60  # 1 hora en segundos
    
    # Mapeo de cultivos a códigos FAO
    CROP_MAPPING = {
        'tomate': '0544',  # Tomatoes
        'papa': '0541',    # Potatoes
        'maiz': '0056',    # Maize
        'frijol': '0176',  # Beans, dry
        'cafe': '0656',    # Coffee, green
        'trigo': '0015',   # Wheat
        'arroz': '0027'    # Rice, paddy
    }
    
    def __init__(self):
        """Inicializa el cliente de FAO"""
        self._cache = {}
        self._last_update = {}
        
    async def _get_prices(self, crop_code: str) -> Optional[pd.DataFrame]:
        """
        Obtiene precios de un cultivo
        Args:
            crop_code: Código FAO del cultivo
        Returns:
            DataFrame con los precios o None si hay error
        """
        try:
            # Construir URL
            url = f"{self.BASE_URL}/datasets/faostat/prices/data"
            
            # Parámetros de la consulta
            params = {
                'area': 'GTM',  # Código ISO para Guatemala
                'item': crop_code,
                'year': f"{datetime.now().year - 5}..{datetime.now().year}",  # Últimos 5 años
                'format': 'json'
            }
            
            # Verificar cache
            cache_key = f"prices_{crop_code}"
            now = datetime.now().timestamp()
            
            if (cache_key in self._cache and 
                now - self._last_update.get(cache_key, 0) <= self.CACHE_DURATION):
                return self._cache[cache_key]
            
            # Hacer request
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Obteniendo precios de {url}")
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    # Parsear JSON
                    data = response.json()
                    
                    # Convertir a DataFrame
                    df = pd.DataFrame(data['data'])
                    
                    # Guardar en cache
                    self._cache[cache_key] = df
                    self._last_update[cache_key] = now
                    
                    return df
                else:
                    logger.error(f"Error {response.status_code} obteniendo precios: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo precios: {str(e)}", exc_info=True)
            return None
            
    async def get_crop_price(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio más reciente de un cultivo
        Args:
            crop_name: Nombre del cultivo en español
        Returns:
            Dict con datos del precio o None si hay error
        """
        try:
            # Normalizar nombre
            crop_name = crop_name.lower().strip()
            
            # Convertir a código FAO
            crop_code = self.CROP_MAPPING.get(crop_name)
            if not crop_code:
                # Buscar coincidencia aproximada
                matches = get_close_matches(crop_name, self.CROP_MAPPING.keys(), n=1, cutoff=0.6)
                if matches:
                    crop_code = self.CROP_MAPPING[matches[0]]
                else:
                    logger.error(f"No se encontró cultivo en FAO: {crop_name}")
                    return None
                    
            # Obtener datos
            df = await self._get_prices(crop_code)
            if df is None:
                return None
                
            # Obtener último precio
            latest = df.iloc[-1]
            
            price_data = {
                'precio': float(latest['value']),
                'unidad': latest['unit'],
                'mercado': 'Nacional',  # FAO provee datos a nivel país
                'departamento': 'Guatemala',
                'fecha': latest['year'],
                'metadata': {
                    'codigo_fao': crop_code,
                    'fuente': 'FAOSTAT',
                    'fecha_actualizacion': datetime.now().isoformat()
                }
            }
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error obteniendo precio: {str(e)}", exc_info=True)
            return None
            
    async def get_historical_prices(self, crop_name: str, years: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene precios históricos de un cultivo
        Args:
            crop_name: Nombre del cultivo en español
            years: Número de años hacia atrás
        Returns:
            Lista de precios históricos o None si hay error
        """
        try:
            # Normalizar nombre
            crop_name = crop_name.lower().strip()
            
            # Convertir a código FAO
            crop_code = self.CROP_MAPPING.get(crop_name)
            if not crop_code:
                matches = get_close_matches(crop_name, self.CROP_MAPPING.keys(), n=1, cutoff=0.6)
                if matches:
                    crop_code = self.CROP_MAPPING[matches[0]]
                else:
                    logger.error(f"No se encontró cultivo en FAO: {crop_name}")
                    return None
                    
            # Obtener datos
            df = await self._get_prices(crop_code)
            if df is None:
                return None
                
            # Filtrar últimos N años
            cutoff_year = datetime.now().year - years
            recent_data = df[df['year'] >= cutoff_year]
            
            # Convertir a lista de diccionarios
            historical_data = []
            
            for _, row in recent_data.iterrows():
                historical_data.append({
                    'precio': float(row['value']),
                    'unidad': row['unit'],
                    'mercado': 'Nacional',
                    'departamento': 'Guatemala',
                    'fecha': str(row['year'])
                })
                
            return historical_data
            
        except Exception as e:
            logger.error(f"Error obteniendo precios históricos: {str(e)}", exc_info=True)
            return None
            
    async def get_available_crops(self) -> Optional[List[str]]:
        """
        Obtiene lista de cultivos disponibles
        Returns:
            Lista de cultivos o None si hay error
        """
        return list(self.CROP_MAPPING.keys())

# Cliente global
fao_client = FAOClient()
