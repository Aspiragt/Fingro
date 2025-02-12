"""
API para obtener precios de productos agrícolas del MAGA usando datos predefinidos
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MagaAPI:
    """Cliente para el API de precios del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA"""
        # Datos predefinidos de cultivos
        self.crops = {
            'maiz': {
                'nombre': 'Maíz',
                'precio': 150.00,
                'unidad': 'quintal',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            },
            'frijol': {
                'nombre': 'Frijol',
                'precio': 500.00,
                'unidad': 'quintal',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            },
            'papa': {
                'nombre': 'Papa',
                'precio': 200.00,
                'unidad': 'quintal',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            },
            'tomate': {
                'nombre': 'Tomate',
                'precio': 250.00,
                'unidad': 'caja',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            },
            'cebolla': {
                'nombre': 'Cebolla',
                'precio': 300.00,
                'unidad': 'quintal',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            },
            'chile': {
                'nombre': 'Chile Pimiento',
                'precio': 350.00,
                'unidad': 'caja',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            },
            'repollo': {
                'nombre': 'Repollo',
                'precio': 100.00,
                'unidad': 'red',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            },
            'zanahoria': {
                'nombre': 'Zanahoria',
                'precio': 180.00,
                'unidad': 'quintal',
                'fecha': '2025-02-12',
                'mercado': 'Nacional',
                'fuente': 'MAGA'
            }
        }
        
        # Mapeo de variaciones de nombres
        self.name_mapping = {
            # Maíz
            'maiz': 'maiz',
            'maíz': 'maiz',
            'mais': 'maiz',
            'maís': 'maiz',
            # Frijol
            'frijol': 'frijol',
            'frijoles': 'frijol',
            'frijol negro': 'frijol',
            'frijoles negros': 'frijol',
            # Papa
            'papa': 'papa',
            'papas': 'papa',
            'patata': 'papa',
            'patatas': 'papa',
            # Tomate
            'tomate': 'tomate',
            'tomates': 'tomate',
            'jitomate': 'tomate',
            # Cebolla
            'cebolla': 'cebolla',
            'cebollas': 'cebolla',
            # Chile
            'chile': 'chile',
            'chiles': 'chile',
            'chile pimiento': 'chile',
            'pimiento': 'chile',
            # Repollo
            'repollo': 'repollo',
            'col': 'repollo',
            # Zanahoria
            'zanahoria': 'zanahoria',
            'zanahorias': 'zanahoria'
        }
        
        logger.info("MagaAPI inicializado con datos predefinidos")
    
    async def search_crop(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Busca un cultivo en los datos predefinidos
        
        Args:
            query: Nombre del cultivo a buscar
            
        Returns:
            Dict con información del cultivo o None si no se encuentra
        """
        try:
            # Normalizar búsqueda
            query = query.lower().strip()
            logger.info(f"Buscando cultivo: {query}")
            
            # Buscar en el mapeo de nombres
            crop_key = self.name_mapping.get(query)
            if not crop_key:
                logger.warning(f"Cultivo no encontrado en mapeo: {query}")
                return None
            
            # Obtener datos del cultivo
            crop_data = self.crops.get(crop_key)
            if not crop_data:
                logger.warning(f"Cultivo no encontrado en datos: {crop_key}")
                return None
            
            logger.info(f"Cultivo encontrado: {crop_data}")
            return crop_data
            
        except Exception as e:
            logger.error(f"Error buscando cultivo: {str(e)}")
            return None
    
    async def get_historical_prices(self, query: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtiene historial de precios para un cultivo
        
        Args:
            query: Nombre del cultivo
            days: Número de días de historial
            
        Returns:
            Lista de precios históricos
        """
        try:
            crop_data = await self.search_crop(query)
            if not crop_data:
                return []
            
            # Por ahora solo retornamos el precio actual
            return [crop_data]
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {str(e)}")
            return []

# Instancia global del API
maga_api = MagaAPI()
