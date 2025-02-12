"""
API para obtener precios de productos agrícolas del MAGA usando datos locales
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class MagaAPI:
    """Cliente para el API de precios del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA"""
        # Intentar diferentes rutas para el archivo
        possible_paths = [
            Path(__file__).parent.parent / 'data' / 'maga_data.json',  # app/data
            Path(__file__).parent.parent.parent / 'app' / 'data' / 'maga_data.json',  # /app/data desde raíz
            Path('/opt/render/project/src/app/data/maga_data.json'),  # Ruta absoluta en Render
        ]
        
        self.data = []
        for path in possible_paths:
            try:
                if path.exists():
                    logger.info(f"Intentando cargar datos desde: {path}")
                    self._load_data(path)
                    if self.data:
                        logger.info(f"Datos cargados exitosamente desde: {path}")
                        break
            except Exception as e:
                logger.error(f"Error cargando datos desde {path}: {str(e)}")
        
        if not self.data:
            logger.error("No se pudieron cargar los datos de MAGA de ninguna ubicación")
            logger.error(f"Directorio actual: {os.getcwd()}")
            logger.error(f"Contenido del directorio: {os.listdir()}")
    
    def _load_data(self, file_path: Path):
        """
        Carga los datos del archivo JSON
        
        Args:
            file_path: Ruta al archivo de datos
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"Datos de MAGA cargados: {len(self.data)} registros")
        except Exception as e:
            logger.error(f"Error cargando datos de MAGA: {str(e)}")
            self.data = []
    
    async def search_crop(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Busca un cultivo en los datos de MAGA
        
        Args:
            query: Nombre del cultivo a buscar
            
        Returns:
            Dict con información del cultivo o None si no se encuentra
        """
        try:
            # Normalizar búsqueda
            query = query.lower().strip()
            query = query.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            
            # Buscar coincidencias
            matches = {}
            for record in self.data:
                product = record.get('producto', '').lower()
                product = product.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                
                if query in product or product in query:
                    key = f"{product}_{record.get('unidad', '')}"
                    if key not in matches or record.get('fecha', '') > matches[key].get('fecha', ''):
                        matches[key] = record
            
            if not matches:
                logger.warning(f"No se encontró el cultivo: {query}")
                return None
            
            # Retornar el registro más reciente
            latest = max(matches.values(), key=lambda x: x.get('fecha', ''))
            result = {
                'nombre': latest.get('producto'),
                'precio': latest.get('precio'),
                'unidad': latest.get('unidad'),
                'fecha': latest.get('fecha'),
                'mercado': latest.get('mercado', 'Nacional'),
                'fuente': 'MAGA'
            }
            logger.info(f"Cultivo encontrado: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error buscando cultivo en MAGA: {str(e)}")
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
            # Normalizar búsqueda
            query = query.lower().strip()
            query = query.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            
            # Buscar coincidencias
            matches = []
            for record in self.data:
                product = record.get('producto', '').lower()
                product = product.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                
                if query in product or product in query:
                    matches.append({
                        'nombre': record.get('producto'),
                        'precio': record.get('precio'),
                        'unidad': record.get('unidad'),
                        'fecha': record.get('fecha'),
                        'mercado': record.get('mercado', 'Nacional'),
                        'fuente': 'MAGA'
                    })
            
            # Ordenar por fecha descendente
            matches.sort(key=lambda x: x.get('fecha', ''), reverse=True)
            
            # Retornar los últimos N días
            return matches[:days]
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de MAGA: {str(e)}")
            return []

# Instancia global del API
maga_api = MagaAPI()
