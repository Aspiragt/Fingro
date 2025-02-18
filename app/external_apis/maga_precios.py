"""
Cliente para obtener precios del MAGA usando datos del archivo JSON
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from app.utils.text import normalize_text, get_crop_variations

logger = logging.getLogger(__name__)

__all__ = [
    'CanalComercializacion',
    'MagaPreciosClient',
    'maga_precios_client'
]

class CanalComercializacion:
    """Tipos de canales de comercialización"""
    MAYORISTA = 'mayorista'
    COOPERATIVA = 'cooperativa'
    EXPORTACION = 'exportacion'
    MERCADO_LOCAL = 'mercado_local'

class MagaPreciosClient:
    """Cliente para obtener precios y costos del MAGA"""
    
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

    def __init__(self, data_file: str = 'maga_data.json'):
        """
        Inicializa el cliente
        
        Args:
            data_file: Ruta al archivo de datos
        """
        self.data_file = data_file
        self._load_data()
        
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

    def _load_data(self):
        """Carga datos del archivo JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            logger.error(f"Error cargando datos: {str(e)}")
            self.data = {}

    def get_rendimiento_cultivo(self, cultivo: str, riego: str) -> float:
        """Obtiene rendimiento base del cultivo en quintales por hectárea"""
        rendimientos_base = {
            'frijol': 25,    # qq/ha
            'maiz': 80,      # qq/ha
            'cafe': 40,      # qq/ha pergamino
            'papa': 350,     # qq/ha
            'tomate': 2000,  # qq/ha
            'chile': 1500,   # qq/ha
            'cebolla': 800,  # qq/ha
            'repollo': 900,  # qq/ha
            'arveja': 150,   # qq/ha
            'aguacate': 300, # qq/ha
            'platano': 700,  # qq/ha
            'limon': 400,    # qq/ha
            'zanahoria': 600,# qq/ha
            'brocoli': 400   # qq/ha
        }
        
        # Factores por tipo de riego
        factores_riego = {
            'goteo': 1.3,
            'aspersion': 1.2,
            'gravedad': 1.1,
            'temporal': 1.0,
            'ninguno': 1.0
        }
        
        rendimiento_base = rendimientos_base.get(cultivo.lower(), 0)
        factor = factores_riego.get(riego.lower(), 1.0)
        
        return rendimiento_base * factor

    def get_costos_cultivo(self, cultivo: str) -> Dict[str, Any]:
        """Obtiene estructura de costos del cultivo"""
        costos = {
            'frijol': {
                'fijos': {
                    'preparacion_terreno': 2000,
                    'sistema_riego': 5000,
                    'herramientas': 1000
                },
                'variables': {
                    'semilla': 800,
                    'fertilizantes': 2000,
                    'pesticidas': 1000,
                    'mano_obra': 5000,
                    'cosecha': 2000,
                    'transporte': 1000
                }
            },
            'maiz': {
                'fijos': {
                    'preparacion_terreno': 2500,
                    'sistema_riego': 5000,
                    'herramientas': 1000
                },
                'variables': {
                    'semilla': 1000,
                    'fertilizantes': 2500,
                    'pesticidas': 1200,
                    'mano_obra': 6000,
                    'cosecha': 2500,
                    'transporte': 1500
                }
            },
            'cafe': {
                'fijos': {
                    'preparacion_terreno': 3000,
                    'sistema_riego': 6000,
                    'herramientas': 2000
                },
                'variables': {
                    'semilla': 2000,
                    'fertilizantes': 3000,
                    'pesticidas': 2000,
                    'mano_obra': 8000,
                    'cosecha': 4000,
                    'transporte': 2000
                }
            },
            'papa': {
                'fijos': {
                    'preparacion_terreno': 3000,
                    'sistema_riego': 6000,
                    'herramientas': 1500
                },
                'variables': {
                    'semilla': 4000,
                    'fertilizantes': 3000,
                    'pesticidas': 2000,
                    'mano_obra': 7000,
                    'cosecha': 3000,
                    'transporte': 2000
                }
            },
            'tomate': {
                'fijos': {
                    'preparacion_terreno': 3500,
                    'sistema_riego': 8000,
                    'herramientas': 2000
                },
                'variables': {
                    'semilla': 5000,
                    'fertilizantes': 4000,
                    'pesticidas': 3000,
                    'mano_obra': 10000,
                    'cosecha': 4000,
                    'transporte': 2500
                }
            }
        }
        
        cultivo = cultivo.lower()
        if cultivo not in costos:
            logger.error(f"No se encontraron costos para el cultivo: {cultivo}")
            raise ValueError(f"Faltan datos del cultivo: {cultivo}")
            
        return costos[cultivo]

    def get_precios_cultivo(self, cultivo: str, channel: str = 'mercado_local') -> Dict[str, Any]:
        """Obtiene precios actuales por canal de venta"""
        precios_base = {
            'frijol': 500,     # Q/qq
            'maiz': 200,       # Q/qq
            'cafe': 1000,      # Q/qq
            'papa': 300,       # Q/qq
            'tomate': 250,     # Q/qq
            'chile': 400,      # Q/qq
            'cebolla': 200,    # Q/qq
            'repollo': 100,    # Q/qq
            'arveja': 600,     # Q/qq
            'aguacate': 450,   # Q/qq
            'platano': 150,    # Q/qq
            'limon': 300,      # Q/qq
            'zanahoria': 200,  # Q/qq
            'brocoli': 300     # Q/qq
        }
        
        cultivo = cultivo.lower()
        if cultivo not in precios_base:
            logger.error(f"No se encontraron precios para el cultivo: {cultivo}")
            raise ValueError(f"Faltan datos del cultivo: {cultivo}")
            
        # Aplicar ajuste por canal
        precio_base = precios_base[cultivo]
        factor = self.price_adjustments.get(channel, 1.0)
        
        return {
            'precio': precio_base * factor,
            'moneda': 'GTQ',
            'unidad': 'quintal',
            'canal': channel
        }

    def calcular_costos_totales(self, cultivo: str, area: float, irrigation: str) -> Dict[str, Any]:
        """Calcula costos totales considerando fijos y variables"""
        try:
            costos = self.get_costos_cultivo(cultivo)
            
            # Costos fijos no dependen del área pero sí del riego
            costos_fijos = sum(costos['fijos'].values())
            if irrigation in ['ninguno', 'temporal']:
                costos_fijos -= costos['fijos']['sistema_riego']
                
            # Costos variables se multiplican por el área
            costos_variables = sum(costos['variables'].values()) * area
            
            return {
                'fijos': costos_fijos,
                'variables': costos_variables,
                'total': costos_fijos + costos_variables
            }
            
        except Exception as e:
            logger.error(f"Error calculando costos para {cultivo}: {str(e)}")
            raise ValueError(f"Error calculando costos: {str(e)}")

    def get_available_crops(self) -> List[str]:
        """
        Obtiene lista de cultivos disponibles
        Returns:
            Lista de cultivos
        """
        return list(set(self.CROP_MAPPING.keys()))

# Cliente global
maga_precios_client = MagaPreciosClient()
