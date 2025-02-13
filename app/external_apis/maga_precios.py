"""
Cliente para obtener precios del MAGA usando datos del archivo JSON
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class CanalComercializacion:
    """Tipos de canales de comercialización"""
    MAYORISTA = 'mayorista'
    COOPERATIVA = 'cooperativa'
    EXPORTACION = 'exportacion'
    MERCADO_LOCAL = 'mercado_local'

class MAGAPreciosClient:
    """Cliente para obtener datos de cultivos del MAGA"""
    
    # Mapeo de cultivos a sus nombres en el JSON
    CROP_MAPPING = {
        'tomate': 'Tomate de cocina',
        'papa': 'Papa',
        'maiz': 'Maíz blanco',
        'frijol': 'Frijol negro',
        'cafe': 'Café',
        'chile': 'Chile pimiento',
        'cebolla': 'Cebolla',
        'repollo': 'Repollo',
        'arveja': 'Arveja china',
        'camote': 'Camote'
    }
    
    def __init__(self):
        """Inicializa el cliente de MAGA Precios"""
        # Cargar precios del JSON
        try:
            json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'maga_data.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                self.maga_prices = json.load(f)
        except Exception as e:
            logger.error(f"Error cargando precios de MAGA: {str(e)}")
            self.maga_prices = []
        
        # Cultivos que típicamente se exportan
        self.export_crops = {
            'cafe', 'arveja', 'aguacate', 'platano', 'limon'
        }
        
        # Cultivos que típicamente se venden a cooperativas
        self.cooperative_crops = {
            'cafe', 'maiz', 'frijol', 'papa'
        }
        
        # Factores de ajuste por canal de comercialización
        self.price_adjustments = {
            CanalComercializacion.MAYORISTA: 1.0,  # Precio base
            CanalComercializacion.COOPERATIVA: 1.1,  # 10% más
            CanalComercializacion.EXPORTACION: 1.3,  # 30% más
            CanalComercializacion.MERCADO_LOCAL: 0.8,  # 20% menos
        }
    
    async def get_crop_price(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio más reciente de un cultivo
        Args:
            crop_name: Nombre del cultivo
        Returns:
            Dict con datos del precio o None si hay error
        """
        try:
            # Normalizar nombre (quitar acentos y convertir a minúsculas)
            import unicodedata
            
            def normalize_text(text: str) -> str:
                """Quita acentos y convierte a minúsculas"""
                text = unicodedata.normalize('NFKD', text)
                text = text.encode('ascii', 'ignore').decode('ascii')
                return text.lower().strip()
            
            crop_name = normalize_text(crop_name)
            
            # Buscar precio en datos de MAGA
            for precio in self.maga_prices:
                producto = normalize_text(precio['Producto'])
                if crop_name in producto:
                    return {
                        'nombre': precio['Producto'],
                        'precio': precio['Precio'],
                        'fecha': precio['Fecha'],
                        'medida': precio['Medida'],
                        'fuente': 'MAGA'
                    }
            
            # Si no se encuentra, buscar en el mapeo
            if crop_name in self.CROP_MAPPING:
                mapped_name = normalize_text(self.CROP_MAPPING[crop_name])
                for precio in self.maga_prices:
                    producto = normalize_text(precio['Producto'])
                    if mapped_name in producto:
                        return {
                            'nombre': precio['Producto'],
                            'precio': precio['Precio'],
                            'fecha': precio['Fecha'],
                            'medida': precio['Medida'],
                            'fuente': 'MAGA'
                        }
            
            logger.warning(f"No se encontró precio para {crop_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo precio para {crop_name}: {str(e)}")
            return None
    
    async def get_available_crops(self) -> list:
        """
        Obtiene lista de cultivos disponibles
        Returns:
            Lista de cultivos
        """
        return list(self.CROP_MAPPING.keys())

# Cliente global
maga_precios_client = MAGAPreciosClient()
