"""
Cliente para obtener precios del MAGA usando datos del archivo JSON
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os
from app.utils.text import normalize_text, get_crop_variations

logger = logging.getLogger(__name__)

class CanalComercializacion:
    """Tipos de canales de comercialización"""
    MAYORISTA = 'mayorista'
    COOPERATIVA = 'cooperativa'
    EXPORTACION = 'exportacion'
    MERCADO_LOCAL = 'mercado_local'

class MAGAPreciosClient:
    """Cliente para obtener datos de cultivos del MAGA"""
    
    # Mapeo de nombres alternativos a nombres estándar
    CROP_MAPPING = {
        'maiz': 'Maíz blanco, de primera',
        'mais': 'Maíz blanco, de primera',
        'máiz': 'Maíz blanco, de primera',
        'máis': 'Maíz blanco, de primera',
        'cafe': 'Café oro, de primera',
        'café': 'Café oro, de primera',
        'frijol': 'Frijol negro, de primera',
        'fríjol': 'Frijol negro, de primera',
        'frejol': 'Frijol negro, de primera',
        'fréjol': 'Frijol negro, de primera',
        'papa': 'Papa, grande, lavada',
        'papas': 'Papa, grande, lavada',
        'tomate': 'Tomate de cocina, grande, de primera',
        'jitomate': 'Tomate de cocina, grande, de primera',
        'chile': 'Chile pimiento, grande, de primera',
        'chiles': 'Chile pimiento, grande, de primera',
        'cebolla': 'Cebolla blanca, mediana, de primera',
        'cebollas': 'Cebolla blanca, mediana, de primera',
        'repollo': 'Repollo blanco, mediano',
        'repollos': 'Repollo blanco, mediano',
        'arveja': 'Arveja china, revuelta, de primera',
        'arvejas': 'Arveja china, revuelta, de primera',
        'aguacate': 'Aguacate Hass, de primera',
        'aguacates': 'Aguacate Hass, de primera',
        'platano': 'Plátano, mediano, de primera',
        'plátano': 'Plátano, mediano, de primera',
        'platanos': 'Plátano, mediano, de primera',
        'plátanos': 'Plátano, mediano, de primera',
        'limon': 'Limón criollo, mediano, de primera',
        'limón': 'Limón criollo, mediano, de primera',
        'limones': 'Limón criollo, mediano, de primera',
        'zanahoria': 'Zanahoria, mediana, de primera',
        'zanahorias': 'Zanahoria, mediana, de primera',
        'brocoli': 'Brócoli, mediano, de primera',
        'brócoli': 'Brócoli, mediano, de primera',
        'brocolis': 'Brócoli, mediano, de primera',
        'brócolis': 'Brócoli, mediano, de primera'
    }
    
    def __init__(self):
        """Inicializa el cliente de MAGA Precios"""
        
        # Cargar precios del JSON
        self.maga_prices = self._load_prices()
        
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
    
    def _load_prices(self):
        try:
            json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'maga_data.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando precios de MAGA: {str(e)}")
            return []
    
    async def get_crop_price(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio más reciente de un cultivo
        Args:
            crop_name: Nombre del cultivo
        Returns:
            Dict con datos del precio o None si hay error
        """
        try:
            # Normalizar nombre del cultivo
            crop_norm = normalize_text(crop_name)
            
            # Buscar en el mapeo
            if crop_norm in self.CROP_MAPPING:
                product_name = self.CROP_MAPPING[crop_norm]
                product_norm = normalize_text(product_name)
                
                # Buscar precio
                for precio in self.maga_prices:
                    if normalize_text(precio['Producto']) == product_norm:
                        return {
                            'nombre': precio['Producto'],
                            'precio': precio['Precio'],
                            'fecha': precio['Fecha'],
                            'medida': precio['Medida'],
                            'fuente': 'MAGA'
                        }
            
            # Si no encontramos, intentar con variaciones
            for variacion in get_crop_variations(crop_name):
                var_norm = normalize_text(variacion)
                if var_norm in self.CROP_MAPPING:
                    product_name = self.CROP_MAPPING[var_norm]
                    product_norm = normalize_text(product_name)
                    
                    for precio in self.maga_prices:
                        if normalize_text(precio['Producto']) == product_norm:
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
