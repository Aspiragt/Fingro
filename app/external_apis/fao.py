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
    
    # Nueva API de FAOSTAT
    BASE_URL = "https://www.fao.org/faostat/api/v1"
    CACHE_DURATION = 24 * 60 * 60  # 24 horas en segundos
    
    # Datos de respaldo para cuando la API no está disponible
    BACKUP_DATA = {
        'tomate': {
            'rendimiento_min': 1800,  # qq/ha
            'rendimiento_max': 2200,  # qq/ha
            'costos_fijos': {'preparacion': 8000, 'siembra': 12000},
            'costos_variables': {'insumos': 15000, 'mano_obra': 20000},
            'ciclo_cultivo': 4,  # meses
            'riesgos': 0.3  # 30% de riesgo
        },
        'maiz': {
            'rendimiento_min': 80,  # qq/ha
            'rendimiento_max': 100,  # qq/ha
            'costos_fijos': {'preparacion': 3000, 'siembra': 2000},
            'costos_variables': {'insumos': 4000, 'mano_obra': 3000},
            'ciclo_cultivo': 4,
            'riesgos': 0.2
        },
        'frijol': {
            'rendimiento_min': 25,  # qq/ha
            'rendimiento_max': 35,  # qq/ha
            'costos_fijos': {'preparacion': 2000, 'siembra': 1500},
            'costos_variables': {'insumos': 3000, 'mano_obra': 2500},
            'ciclo_cultivo': 3,
            'riesgos': 0.25
        },
        'papa': {
            'rendimiento_min': 300,  # qq/ha
            'rendimiento_max': 400,  # qq/ha
            'costos_fijos': {'preparacion': 5000, 'siembra': 4000},
            'costos_variables': {'insumos': 8000, 'mano_obra': 6000},
            'ciclo_cultivo': 4,
            'riesgos': 0.2
        },
        'cafe': {
            'rendimiento_min': 20,  # qq/ha
            'rendimiento_max': 30,  # qq/ha
            'costos_fijos': {'preparacion': 15000, 'siembra': 20000},
            'costos_variables': {'insumos': 25000, 'mano_obra': 30000},
            'ciclo_cultivo': 12,
            'riesgos': 0.15
        }
    }
    
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
            
            # Normalizar nombre
            crop_name = crop_name.lower().strip()
            
            # Buscar en datos de respaldo
            for backup_name, data in self.BACKUP_DATA.items():
                if crop_name in backup_name or backup_name in crop_name:
                    logger.info(f"Usando datos de respaldo para {crop_name}")
                    return {
                        **data,
                        'metadata': {
                            'nombre': backup_name,
                            'fuente': 'datos históricos',
                            'fecha': datetime.now().strftime('%Y-%m-%d')
                        }
                    }
            
            # Si no hay coincidencia exacta, buscar aproximada
            matches = get_close_matches(crop_name, self.BACKUP_DATA.keys(), n=1, cutoff=0.6)
            if matches:
                matched_name = matches[0]
                logger.info(f"Usando datos de respaldo para {crop_name} (coincidencia: {matched_name})")
                return {
                    **self.BACKUP_DATA[matched_name],
                    'metadata': {
                        'nombre': matched_name,
                        'fuente': 'datos históricos',
                        'fecha': datetime.now().strftime('%Y-%m-%d'),
                        'coincidencia_aproximada': True
                    }
                }
            
            logger.warning(f"No se encontraron datos para el cultivo: {crop_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del cultivo: {str(e)}", exc_info=True)
            return None

# Cliente global
fao_client = FAOClient()
