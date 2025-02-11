"""
Cliente para la API de FAOSTAT
"""
import httpx
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import json
import os
from difflib import get_close_matches
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
            },
            timeout=30.0  # 30 segundos de timeout
        )
        self._cache = {}
        self._last_update = {}
        self._crops_cache = None
        self._crops_last_update = 0
        
    async def _get_all_crops(self) -> Dict[str, str]:
        """
        Obtiene la lista completa de cultivos de FAOSTAT
        Returns:
            Dict[str, str]: Mapeo de nombres de cultivos a códigos
        """
        try:
            now = datetime.now().timestamp()
            
            # Verificar cache
            if self._crops_cache and now - self._crops_last_update < self.CACHE_DURATION:
                logger.debug("Usando cache de cultivos")
                return self._crops_cache
            
            logger.info("Obteniendo lista de cultivos de FAOSTAT...")
            
            # Obtener lista de cultivos de FAOSTAT
            async with self.session as client:
                response = await client.get(
                    f"{self.BASE_URL}/definitions/items",
                    params={
                        'dataset': 'production',
                        'language': 'es',
                        'show_lists': 'true'
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error obteniendo cultivos: {response.status_code} - {response.text}")
                    return {}
                
                data = response.json()
                if not data or 'data' not in data:
                    logger.error("Respuesta de FAOSTAT sin datos")
                    return {}
                
                # Filtrar solo cultivos primarios
                crops = {
                    item['label']: item['code']
                    for item in data['data']
                    if 'Primary' in item.get('group', '')
                    and not any(x in item['label'].lower() for x in ['total', 'otros', 'nes'])
                }
                
                logger.info(f"Se encontraron {len(crops)} cultivos")
                logger.debug(f"Cultivos encontrados: {list(crops.keys())[:10]}...")
                
                # Actualizar cache
                self._crops_cache = crops
                self._crops_last_update = now
                
                return crops
                
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con FAOSTAT: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo cultivos: {str(e)}", exc_info=True)
            return {}
            
    async def _get_production_data(self, crop_code: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de producción para un cultivo específico
        Args:
            crop_code: Código del cultivo en FAOSTAT
        Returns:
            Dict con datos de producción o None si hay error
        """
        try:
            logger.info(f"Obteniendo datos de producción para cultivo {crop_code}")
            
            async with self.session as client:
                response = await client.get(
                    f"{self.BASE_URL}/data/dataset/production",
                    params={
                        'item_code': crop_code,
                        'area': 'GTM',  # Guatemala
                        'element': ['5510', '5419'],  # Producción y Rendimiento
                        'year': ['2020', '2021', '2022'],
                        'show_lists': 'false',
                        'show_units': 'true'
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error obteniendo producción: {response.status_code} - {response.text}")
                    return None
                    
                data = response.json()
                if not data or 'data' not in data:
                    logger.error("Respuesta de producción sin datos")
                    return None
                    
                logger.info(f"Datos de producción obtenidos: {len(data['data'])} registros")
                return data
                
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con FAOSTAT: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo producción: {str(e)}", exc_info=True)
            return None
            
    async def get_crop_data(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene todos los datos relevantes para un cultivo
        Args:
            crop_name: Nombre del cultivo en español
        Returns:
            Dict con datos del cultivo o None si hay error
        """
        try:
            logger.info(f"Buscando datos para cultivo: {crop_name}")
            
            # Obtener lista de cultivos
            crops = await self._get_all_crops()
            if not crops:
                logger.error("No se pudo obtener lista de cultivos")
                return None
                
            # Buscar coincidencias
            crop_name = crop_name.lower().strip()
            matches = get_close_matches(crop_name, crops.keys(), n=1, cutoff=0.6)
            
            if not matches:
                logger.error(f"No se encontraron coincidencias para: {crop_name}")
                return None
                
            matched_crop = matches[0]
            crop_code = crops[matched_crop]
            
            logger.info(f"Coincidencia encontrada: {matched_crop} (código: {crop_code})")
            
            # Obtener datos de producción
            production_data = await self._get_production_data(crop_code)
            if not production_data:
                logger.error(f"No se pudieron obtener datos de producción para: {matched_crop}")
                return None
                
            # Procesar datos
            # TODO: Implementar procesamiento de datos
            processed_data = {
                'rendimiento_min': 20,  # qq/ha
                'rendimiento_max': 30,  # qq/ha
                'costos_fijos': {'preparacion': 2000, 'siembra': 3000},
                'costos_variables': {'insumos': 5000, 'mano_obra': 4000},
                'ciclo_cultivo': 4,  # meses
                'riesgos': 0.2,  # 20% de riesgo
                'metadata': {
                    'nombre_fao': matched_crop,
                    'codigo_fao': crop_code,
                    'fuente': 'FAOSTAT'
                }
            }
            
            logger.info(f"Datos procesados para {matched_crop}: {processed_data}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del cultivo: {str(e)}", exc_info=True)
            return None

# Cliente global
fao_client = FAOClient()
