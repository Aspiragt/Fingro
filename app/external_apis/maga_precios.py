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
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        except Exception as e:
            logger.error(f"Error cargando datos: {str(e)}")
            self.data = {
                'cultivos': {},
                'precios': {},
                'costos': {}
            }
            
    def get_costos_cultivo(self, cultivo: str) -> Dict[str, Any]:
        """Obtiene costos de producción para un cultivo"""
        costos = {
            'frijol': {
                'costos_fijos': {
                    'preparacion_tierra': 800,    # Maquinaria/herramientas
                    'asistencia_tecnica': 500,    # Por ciclo
                    'administracion': 400,        # Por ciclo
                    'imprevistos': 300           # Por ciclo
                },
                'costos_por_hectarea': {
                    'semilla': 1200,             # 60 lb/ha a Q20/lb
                    'fertilizantes': 1500,       # NPK + foliar
                    'pesticidas': 800,           # Herbicidas + insecticidas
                    'mano_obra': 2000,           # Siembra, fumigación, cosecha
                    'riego': {
                        'temporal': 0,
                        'gravedad': 500,
                        'aspersion': 800,
                        'goteo': 1200
                    }
                },
                'rendimiento_por_hectarea': 35,  # quintales/ha
                'merma': 0.05                    # 5% pérdida
            },
            'maiz': {
                'costos_fijos': {
                    'preparacion_tierra': 1000,
                    'asistencia_tecnica': 500,
                    'administracion': 400,
                    'imprevistos': 300
                },
                'costos_por_hectarea': {
                    'semilla': 1500,             # Semilla certificada
                    'fertilizantes': 2000,
                    'pesticidas': 1000,
                    'mano_obra': 2500,
                    'riego': {
                        'temporal': 0,
                        'gravedad': 600,
                        'aspersion': 900,
                        'goteo': 1400
                    }
                },
                'rendimiento_por_hectarea': 45,
                'merma': 0.08
            }
        }
        return costos.get(cultivo, {})
    
    def calcular_costos_totales(self, cultivo: str, area: float, irrigation: str) -> Dict[str, float]:
        """Calcula costos totales considerando fijos y variables"""
        costos = self.get_costos_cultivo(cultivo)
        if not costos:
            return {}

        # Costos fijos (no dependen del área)
        costos_fijos = sum(costos.get('costos_fijos', {}).values())

        # Costos por hectárea
        costos_ha = costos.get('costos_por_hectarea', {})
        costo_riego = costos_ha.get('riego', {}).get(irrigation, 0)
        
        # Suma de costos por hectárea sin riego
        costos_ha_sin_riego = sum(v for k, v in costos_ha.items() if k != 'riego')
        
        # Costos variables totales (dependen del área)
        costos_variables = (costos_ha_sin_riego + costo_riego) * area

        return {
            'costos_fijos': costos_fijos,
            'costos_variables': costos_variables,
            'costos_totales': costos_fijos + costos_variables
        }
    
    def get_precios_cultivo(self, cultivo: str, channel: str = 'mercado_local') -> Dict[str, float]:
        """Obtiene precios actuales por canal de venta"""
        precios_base = {
            'frijol': 550,  # Q/quintal
            'maiz': 450     # Q/quintal
        }
        
        # Factores por canal
        factores_canal = {
            'mercado_local': 1.0,
            'cooperativa': 1.15,
            'mayorista': 1.2,
            'exportacion': 1.3
        }
        
        precio_base = precios_base.get(cultivo, 0)
        factor = factores_canal.get(channel, 1.0)
        
        return {
            'precio_actual': precio_base * factor,
            'precio_minimo': precio_base * 0.8,
            'precio_maximo': precio_base * 1.4
        }
    
    def get_precios_cultivo_original(self, cultivo: str, canal: str = 'mayorista') -> Dict[str, Any]:
        """
        Obtiene precios actuales para un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            canal: Canal de comercialización
            
        Returns:
            dict: Datos de precios o None si no existe
        """
        try:
            cultivo = normalize_text(cultivo)
            canal = normalize_text(canal)
            
            # Precios base por quintal
            precios_base = {
                'maiz': 200,
                'frijol': 500,
                'cafe': 1000,
                'tomate': 300,
                'papa': 250
            }
            
            # Factores por canal
            factores_canal = {
                'mercado_local': 0.9,  # 10% menos que mayorista
                'mayorista': 1.0,  # Precio base
                'cooperativa': 1.1,  # 10% más que mayorista
                'exportacion': 1.3  # 30% más que mayorista
            }
            
            # Calcular precio
            precio_base = precios_base.get(cultivo)
            if not precio_base:
                return None
                
            factor = factores_canal.get(canal, 1.0)
            precio_actual = precio_base * factor
            
            return {
                'precio_actual': precio_actual,
                'precio_base': precio_base,
                'tendencia': 'estable'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo precios: {str(e)}")
            return None
            
    def get_cultivos_region(self, region: str) -> List[str]:
        """
        Obtiene cultivos recomendados para una región
        
        Args:
            region: Nombre de la región o departamento
            
        Returns:
            list: Lista de cultivos recomendados
        """
        try:
            region = normalize_text(region)
            
            # Cultivos por región
            cultivos_region = {
                'guatemala': ['maiz', 'frijol', 'tomate'],
                'peten': ['maiz', 'frijol'],
                'alta_verapaz': ['cafe', 'cardamomo'],
                'escuintla': ['caña', 'platano'],
                'san_marcos': ['cafe', 'papa']
            }
            
            return cultivos_region.get(region, ['maiz', 'frijol'])  # Cultivos default
            
        except Exception as e:
            logger.error(f"Error obteniendo cultivos: {str(e)}")
            return ['maiz', 'frijol']  # Cultivos default
            
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
                for precio in self.data['precios']:
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
                    
                    for precio in self.data['precios']:
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
