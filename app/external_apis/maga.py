"""
Módulo para obtener información de precios del MAGA
"""
import logging
from typing import Dict, Any, Optional, List, Union
import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime, timedelta
import re
from cachetools import TTLCache
from app.config import settings
from app.utils.constants import CROP_VARIATIONS

logger = logging.getLogger(__name__)

class MagaAPI:
    """Cliente para obtener información de precios del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA"""
        self.base_url = settings.MAGA_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        self.ua = UserAgent()
        
        # Caché de precios con TTL de 6 horas
        self.price_cache = TTLCache(maxsize=100, ttl=21600)
        
        # Precios por defecto (en quetzales por quintal)
        self.default_prices = {
            'maiz': 150,
            'frijol': 500,
            'papa': 200,
            'tomate': 300,
            'chile': 400,
            'cebolla': 250,
            'zanahoria': 200,
            'aguacate': 450,
            'platano': 150,
            'cafe': 1000,
            'arroz': 350,
            'brocoli': 300,
            'lechuga': 200,
            'repollo': 150,
            'arveja': 400
        }
    
    async def get_precio_cultivo(self, cultivo: str) -> float:
        """
        Obtiene el precio actual de un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            float: Precio por quintal en quetzales
        """
        try:
            # Normalizar nombre del cultivo
            cultivo = cultivo.lower().strip()
            
            # Verificar si es un cultivo conocido
            cultivo_normalizado = None
            for nombre, variaciones in CROP_VARIATIONS.items():
                if cultivo in variaciones:
                    cultivo_normalizado = nombre
                    break
            
            if not cultivo_normalizado:
                logger.warning(f"Cultivo no reconocido: {cultivo}")
                return self.default_prices.get('maiz', 150)  # Precio base maíz
            
            # Verificar caché
            if cultivo_normalizado in self.price_cache:
                return self.price_cache[cultivo_normalizado]
            
            # Obtener precio de la web
            try:
                precio = await self._fetch_precio_web(cultivo_normalizado)
                if precio:
                    self.price_cache[cultivo_normalizado] = precio
                    return precio
            except Exception as e:
                logger.error(f"Error obteniendo precio web para {cultivo_normalizado}: {str(e)}")
            
            # Si no se encuentra, usar precio por defecto
            precio_default = self.default_prices.get(cultivo_normalizado, 150)
            logger.info(f"Usando precio por defecto para {cultivo_normalizado}: Q{precio_default}")
            return precio_default
            
        except Exception as e:
            logger.error(f"Error en get_precio_cultivo para {cultivo}: {str(e)}")
            return self.default_prices.get('maiz', 150)  # Precio base maíz
    
    async def _fetch_precio_web(self, cultivo: str) -> Optional[float]:
        """
        Obtiene el precio de un cultivo desde la web del MAGA
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            Optional[float]: Precio por quintal si se encuentra
        """
        try:
            # Construir URL
            url = f"{self.base_url}/precios"
            
            # Headers para simular navegador
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html',
                'Accept-Language': 'es-GT,es',
            }
            
            # Realizar request
            async with self.client as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Parsear HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar precio
                for row in soup.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        nombre = cells[0].text.strip().lower()
                        if self._match_cultivo(cultivo, nombre):
                            precio = self._extract_precio(cells[1].text)
                            if precio:
                                return precio
            
            return None
            
        except Exception as e:
            logger.error(f"Error en _fetch_precio_web para {cultivo}: {str(e)}")
            return None
    
    def _match_cultivo(self, cultivo: str, nombre: str) -> bool:
        """
        Verifica si el nombre del cultivo coincide con alguna variación
        
        Args:
            cultivo: Nombre del cultivo a buscar
            nombre: Nombre encontrado en la web
            
        Returns:
            bool: True si hay coincidencia
        """
        try:
            variaciones = CROP_VARIATIONS.get(cultivo, [])
            return any(var in nombre for var in variaciones)
        except Exception:
            return False
    
    def _extract_precio(self, texto: str) -> Optional[float]:
        """
        Extrae el precio de un texto
        
        Args:
            texto: Texto que contiene el precio
            
        Returns:
            Optional[float]: Precio extraído o None si no se encuentra
        """
        try:
            # Buscar números en el texto
            match = re.search(r'Q?(\d+(?:\.\d{1,2})?)', texto)
            if match:
                return float(match.group(1))
            return None
        except Exception:
            return None

# Instancia global
maga_api = MagaAPI()
