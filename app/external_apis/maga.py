"""
Integración con el Sistema de Información de Mercados del MAGA
"""
import httpx
from typing import List, Optional
import pandas as pd
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class MAGAClient:
    """Cliente para obtener datos del Sistema de Información de Mercados del MAGA"""
    
    BASE_URL = "https://precios.maga.gob.gt/datos-abiertos"
    
    # Precios de respaldo (por quintal)
    BACKUP_PRICES = {
        'tomate': {'precio_actual': 200, 'tendencia': 'estable', 'unidad_medida': 'caja'},
        'maiz': {'precio_actual': 180, 'tendencia': 'alza', 'unidad_medida': 'quintal'},
        'frijol': {'precio_actual': 500, 'tendencia': 'estable', 'unidad_medida': 'quintal'},
        'papa': {'precio_actual': 300, 'tendencia': 'baja', 'unidad_medida': 'quintal'},
        'cebolla': {'precio_actual': 250, 'tendencia': 'estable', 'unidad_medida': 'quintal'},
        'chile': {'precio_actual': 400, 'tendencia': 'alza', 'unidad_medida': 'caja'},
        'zanahoria': {'precio_actual': 150, 'tendencia': 'estable', 'unidad_medida': 'quintal'},
        'aguacate': {'precio_actual': 350, 'tendencia': 'alza', 'unidad_medida': 'caja'},
        'cafe': {'precio_actual': 1200, 'tendencia': 'estable', 'unidad_medida': 'quintal'},
        'arroz': {'precio_actual': 400, 'tendencia': 'estable', 'unidad_medida': 'quintal'}
    }
    
    def __init__(self):
        """Inicializa el cliente"""
        self.session = httpx.AsyncClient()
        self._precios_cache = {}
        self._last_update = None
    
    async def get_precio_cultivo(self, cultivo: str) -> Optional[dict]:
        """
        Obtiene el precio actual y tendencia de un cultivo
        
        Args:
            cultivo: Nombre del cultivo a buscar
            
        Returns:
            dict con información del precio o None si no se encuentra
        """
        try:
            # Normalizar nombre del cultivo
            cultivo = cultivo.lower().strip()
            
            # Actualizar cache si es necesario (cada 24 horas)
            if self._necesita_actualizar_cache():
                await self._actualizar_cache()
            
            # Primero intentar obtener de la API
            if cultivo in self._precios_cache:
                data = self._precios_cache[cultivo]
                logger.info(f"Precio encontrado en cache para {cultivo}: {data}")
                return {
                    'precio_actual': data['precio_actual'],
                    'tendencia': data['tendencia'],
                    'unidad_medida': data['unidad_medida'],
                    'ultima_actualizacion': data['ultima_actualizacion'],
                    'fuente': 'MAGA'
                }
                
            # Si no está en cache, buscar en precios de respaldo
            if cultivo in self.BACKUP_PRICES:
                data = self.BACKUP_PRICES[cultivo]
                logger.info(f"Usando precio de respaldo para {cultivo}: {data}")
                return {
                    **data,
                    'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d'),
                    'fuente': 'histórico'
                }
                
            # Si no se encuentra en ninguna fuente
            logger.warning(f"No se encontró precio para {cultivo}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo precio para {cultivo}: {str(e)}")
            
            # En caso de error, intentar usar precio de respaldo
            if cultivo in self.BACKUP_PRICES:
                data = self.BACKUP_PRICES[cultivo]
                logger.info(f"Usando precio de respaldo después de error para {cultivo}: {data}")
                return {
                    **data,
                    'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d'),
                    'fuente': 'histórico'
                }
            return None
            
    def _necesita_actualizar_cache(self) -> bool:
        """Verifica si es necesario actualizar el cache"""
        if not self._last_update:
            return True
        return datetime.now() - self._last_update > timedelta(hours=24)
        
    async def _actualizar_cache(self):
        """Actualiza el cache de precios desde la API"""
        try:
            # TODO: Implementar llamada real a la API
            pass
        except Exception as e:
            logger.error(f"Error actualizando cache: {str(e)}")

# Cliente global
maga_client = MAGAClient()
