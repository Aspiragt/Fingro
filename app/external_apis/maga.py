"""
Módulo para obtener información de precios del MAGA
"""
import logging
from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
import re
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class MagaAPI:
    """Cliente para obtener información de precios del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA"""
        self.base_url = "https://precios.maga.gob.gt/informes"
        self.ua = UserAgent()
        # Caché de precios con TTL de 6 horas
        self.price_cache = TTLCache(maxsize=100, ttl=21600)
        
        # Mapeo de nombres comunes de cultivos
        self.crop_mapping = {
            'maiz': ['maíz', 'maiz', 'elote'],
            'frijol': ['frijol', 'frijoles', 'frijol negro'],
            'papa': ['papa', 'papas', 'patata'],
            'tomate': ['tomate', 'tomates'],
            'chile': ['chile', 'chiles', 'chile pimiento'],
            'cebolla': ['cebolla', 'cebollas'],
            'zanahoria': ['zanahoria', 'zanahorias'],
            'aguacate': ['aguacate', 'aguacates', 'avocado'],
            'platano': ['plátano', 'platano', 'banano'],
            'cafe': ['café', 'cafe', 'coffee'],
            'arroz': ['arroz', 'rice'],
            'brocoli': ['brócoli', 'brocoli', 'broccoli'],
            'lechuga': ['lechuga', 'lechugas'],
            'repollo': ['repollo', 'col'],
            'arveja': ['arveja', 'arvejas', 'guisantes']
        }
        
        # Datos de precios por defecto (actualizados regularmente)
        self.default_prices = {
            'granos': {
                'precio_bajo': 120,
                'precio_alto': 180,
                'unidad': 'quintal'
            },
            'verduras': {
                'precio_bajo': 200,
                'precio_alto': 300,
                'unidad': 'quintal'
            },
            'frutas': {
                'precio_bajo': 250,
                'precio_alto': 350,
                'unidad': 'quintal'
            }
        }
        
        # Clasificación de cultivos
        self.crop_categories = {
            'granos': ['maiz', 'frijol', 'arroz', 'cafe'],
            'verduras': ['papa', 'tomate', 'chile', 'cebolla', 'zanahoria', 'brocoli', 'lechuga', 'repollo', 'arveja'],
            'frutas': ['aguacate', 'platano']
        }
    
    def _normalize_crop_name(self, crop: str) -> Optional[str]:
        """Normaliza el nombre del cultivo"""
        crop = crop.lower().strip()
        for base_name, variations in self.crop_mapping.items():
            if crop in variations or crop == base_name:
                return base_name
        return None
    
    def _get_crop_category(self, crop: str) -> str:
        """Obtiene la categoría del cultivo"""
        for category, crops in self.crop_categories.items():
            if crop in crops:
                return category
        return 'granos'  # categoría por defecto
    
    async def get_crop_prices(self, crop_name: str) -> Dict[str, Any]:
        """
        Obtiene los precios actuales para un cultivo
        """
        try:
            # Normalizar nombre del cultivo
            normalized_crop = self._normalize_crop_name(crop_name)
            
            # Verificar caché
            cache_key = f"price_{normalized_crop if normalized_crop else crop_name}"
            if cache_key in self.price_cache:
                logger.info(f"Usando precios en caché para {crop_name}")
                return self.price_cache[cache_key]
            
            # Intentar obtener precios del MAGA
            prices = await self._scrape_prices(normalized_crop if normalized_crop else crop_name)
            
            if not prices:
                # Si no se encuentran precios, usar valores por defecto
                category = self._get_crop_category(normalized_crop if normalized_crop else crop_name)
                default_data = self.default_prices[category]
                
                prices = {
                    'cultivo': crop_name,
                    'precio_actual': (default_data['precio_bajo'] + default_data['precio_alto']) / 2,
                    'precio_bajo': default_data['precio_bajo'],
                    'precio_alto': default_data['precio_alto'],
                    'unidad_medida': default_data['unidad'],
                    'tendencia': 'estable',
                    'fuente': 'estimación',
                    'fecha_actualizacion': datetime.now().isoformat()
                }
            
            # Guardar en caché
            self.price_cache[cache_key] = prices
            return prices
            
        except Exception as e:
            logger.error(f"Error obteniendo precios para {crop_name}: {str(e)}")
            # Retornar datos por defecto en caso de error
            return {
                'cultivo': crop_name,
                'precio_actual': 150,
                'precio_bajo': 120,
                'precio_alto': 180,
                'unidad_medida': 'quintal',
                'tendencia': 'estable',
                'fuente': 'estimación por error',
                'fecha_actualizacion': datetime.now().isoformat()
            }
    
    async def _scrape_prices(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """
        Intenta obtener precios del sitio del MAGA
        """
        try:
            headers = {'User-Agent': self.ua.random}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, headers=headers, timeout=10.0)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Buscar la tabla de precios
                price_table = soup.find('table', {'class': 'precios'})
                if not price_table:
                    return None
                
                # Buscar el cultivo en la tabla
                for row in price_table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        product_name = cells[0].text.strip().lower()
                        if crop_name in product_name:
                            try:
                                # Extraer precios
                                price_text = cells[1].text.strip()
                                price_match = re.search(r'Q\s*(\d+(?:\.\d+)?)', price_text)
                                price = float(price_match.group(1)) if price_match else 0
                                
                                # Extraer unidad de medida
                                unit = cells[2].text.strip()
                                
                                # Determinar tendencia
                                trend_cell = cells[3].text.strip().lower()
                                if 'subi' in trend_cell or 'alza' in trend_cell:
                                    trend = 'alza'
                                elif 'baj' in trend_cell:
                                    trend = 'baja'
                                else:
                                    trend = 'estable'
                                
                                return {
                                    'cultivo': crop_name,
                                    'precio_actual': price,
                                    'precio_bajo': price * 0.8,  # Estimado
                                    'precio_alto': price * 1.2,  # Estimado
                                    'unidad_medida': unit,
                                    'tendencia': trend,
                                    'fuente': 'MAGA',
                                    'fecha_actualizacion': datetime.now().isoformat()
                                }
                            except Exception as e:
                                logger.error(f"Error procesando datos de precio: {str(e)}")
                                return None
                
                return None
                
        except Exception as e:
            logger.error(f"Error haciendo scraping de precios: {str(e)}")
            return None

# Instancia global
maga_api = MagaAPI()
