"""
Cliente para obtener datos de precios del MAGA (Ministerio de Agricultura, Ganadería y Alimentación)
https://precios.maga.gob.gt/
"""
import httpx
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
import json
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
from difflib import get_close_matches

logger = logging.getLogger(__name__)

class MAGAClient:
    """Cliente para obtener datos de precios del MAGA"""
    
    BASE_URL = "https://precios.maga.gob.gt"
    CACHE_DURATION = 6 * 60 * 60  # 6 horas en segundos
    
    # Mapeo de cultivos a nombres MAGA
    CROP_MAPPING = {
        'tomate': ['tomate de cocina', 'tomate manzano', 'tomate de tierra'],
        'papa': ['papa', 'papa larga', 'papa revuelta', 'papa suprema'],
        'maiz': ['maíz blanco', 'maiz blanco', 'maiz amarillo', 'maíz amarillo'],
        'frijol': ['frijol negro', 'frijol rojo', 'frijol colorado'],
        'cafe': ['café', 'cafe'],
        'trigo': ['trigo'],
        'arroz': ['arroz', 'arroz oro', 'arroz blanco']
    }
    
    def __init__(self):
        """Inicializa el cliente de MAGA"""
        self._cache = {}
        self._last_update = {}
        self._user_agent = UserAgent()
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Genera headers aleatorios para evitar bloqueos
        Returns:
            Dict con headers HTTP
        """
        return {
            'User-Agent': self._user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-GT,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        }
        
    async def _get_prices(self) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene precios actuales del MAGA
        Returns:
            Lista de precios o None si hay error
        """
        try:
            # Verificar cache
            cache_key = "prices"
            now = datetime.now().timestamp()
            
            if (cache_key in self._cache and 
                now - self._last_update.get(cache_key, 0) <= self.CACHE_DURATION):
                return self._cache[cache_key]
            
            # Hacer request
            url = f"{self.BASE_URL}/diarios/diarios.html"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Obteniendo precios de {url}")
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    # Parsear HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Obtener fecha
                    date_text = soup.find('h5')
                    if not date_text:
                        logger.error("No se encontró la fecha en el HTML")
                        return None
                        
                    date_text = date_text.text.strip()
                    logger.info(f"Fecha encontrada: {date_text}")
                    date = datetime.strptime(date_text, '%d/%m/%Y')
                    
                    # Obtener tabla de precios
                    prices = []
                    rows = soup.find_all('tr')
                    
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 4:  # Producto, Mercado, Medida, Precio
                            # Limpiar y normalizar texto
                            product = cols[0].text.strip().lower()
                            market = cols[1].text.strip()
                            unit = cols[2].text.strip()
                            price_text = cols[3].text.strip().replace('Q', '').replace(',', '')
                            
                            try:
                                price = float(price_text)
                            except ValueError:
                                logger.warning(f"No se pudo convertir precio: {price_text}")
                                continue
                                
                            prices.append({
                                'producto': product,
                                'mercado': market,
                                'unidad': unit,
                                'precio': price,
                                'fecha': date.strftime('%Y-%m-%d')
                            })
                    
                    logger.info(f"Total de precios encontrados: {len(prices)}")
                    
                    # Guardar en cache
                    self._cache[cache_key] = prices
                    self._last_update[cache_key] = now
                    
                    return prices
                else:
                    logger.error(f"Error {response.status_code} obteniendo precios: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo precios: {str(e)}", exc_info=True)
            return None
            
    def _find_matching_products(self, crop_name: str, prices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Encuentra productos que coincidan con el cultivo
        Args:
            crop_name: Nombre del cultivo
            prices: Lista de precios
        Returns:
            Lista de precios que coinciden
        """
        # Obtener variantes del cultivo
        crop_variants = self.CROP_MAPPING.get(crop_name, [crop_name])
        logger.info(f"Buscando coincidencias para: {crop_name} (variantes: {crop_variants})")
        
        # Buscar coincidencias
        matches = []
        for price in prices:
            product = price['producto']
            
            # Verificar coincidencia exacta
            if any(variant in product for variant in crop_variants):
                logger.debug(f"Coincidencia exacta: {product}")
                matches.append(price)
                continue
                
            # Verificar coincidencia aproximada
            for variant in crop_variants:
                if get_close_matches(variant, [product], n=1, cutoff=0.8):
                    logger.debug(f"Coincidencia aproximada: {product}")
                    matches.append(price)
                    break
                    
        logger.info(f"Encontradas {len(matches)} coincidencias para {crop_name}")
        return matches
            
    async def get_crop_price(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio más reciente de un cultivo
        Args:
            crop_name: Nombre del cultivo en español
        Returns:
            Dict con datos del precio o None si hay error
        """
        try:
            # Normalizar nombre
            crop_name = crop_name.lower().strip()
            
            # Obtener precios
            prices = await self._get_prices()
            if not prices:
                logger.error(f"No se pudieron obtener precios del MAGA")
                return None
                
            # Buscar coincidencias
            matches = self._find_matching_products(crop_name, prices)
            if not matches:
                logger.warning(f"No se encontró el cultivo '{crop_name}' en MAGA")
                return None
                
            # Obtener precio promedio del día
            total = sum(m['precio'] for m in matches)
            avg_price = total / len(matches)
            
            # Usar el primer match como base
            price_data = {
                'producto': matches[0]['producto'],
                'mercado': matches[0]['mercado'],
                'unidad': matches[0]['unidad'],
                'precio': avg_price,
                'fecha': matches[0]['fecha'],
                'metadata': {
                    'total_matches': len(matches),
                    'variants': self.CROP_MAPPING.get(crop_name, [crop_name]),
                    'all_prices': [m['precio'] for m in matches],
                    'all_markets': list(set(m['mercado'] for m in matches))
                }
            }
            
            return price_data
                
        except Exception as e:
            logger.error(f"Error obteniendo precio de {crop_name}: {str(e)}", exc_info=True)
            return None
            
    async def get_historical_prices(self, crop_name: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene precios históricos de un cultivo
        Args:
            crop_name: Nombre del cultivo en español
            days: Número de días hacia atrás (máximo 30)
        Returns:
            Lista de precios históricos o None si hay error
        """
        # Por ahora solo retornamos el precio actual ya que necesitaríamos
        # implementar scraping del histórico
        try:
            price = await self.get_crop_price(crop_name)
            return [price] if price else None
        except Exception as e:
            logger.error(f"Error obteniendo precios históricos: {str(e)}", exc_info=True)
            return None
            
    async def get_available_crops(self) -> Optional[List[str]]:
        """
        Obtiene lista de cultivos disponibles
        Returns:
            Lista de cultivos o None si hay error
        """
        return list(self.CROP_MAPPING.keys())

# Cliente global
maga_client = MAGAClient()
