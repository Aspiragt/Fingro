"""
API para obtener precios de productos agrícolas del MAGA usando datos locales
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class MagaAPI:
    """Cliente para el API de precios del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA"""
        self.data_file = Path(__file__).parent.parent.parent / 'maga_data.json'
        self._load_data()
    
    def _load_data(self):
        """Carga los datos del archivo JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
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
            
            # Buscar coincidencias
            matches = {}
            for record in self.data:
                product = record.get('producto', '').lower()
                if query in product or product in query:
                    key = f"{product}_{record.get('unidad', '')}"
                    if key not in matches or record.get('fecha', '') > matches[key].get('fecha', ''):
                        matches[key] = record
            
            if not matches:
                return None
            
            # Retornar el registro más reciente
            latest = max(matches.values(), key=lambda x: x.get('fecha', ''))
            return {
                'nombre': latest.get('producto'),
                'precio': latest.get('precio'),
                'unidad': latest.get('unidad'),
                'fecha': latest.get('fecha'),
                'mercado': latest.get('mercado', 'Nacional'),
                'fuente': 'MAGA'
            }
            
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
            
            # Buscar coincidencias
            matches = []
            for record in self.data:
                product = record.get('producto', '').lower()
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
