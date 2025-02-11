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
            
            # Verificar caché
            if cultivo in self.price_cache:
                return self.price_cache[cultivo]
            
            # Obtener precio de la web
            precio = await self._fetch_precio_web(cultivo)
            if precio:
                self.price_cache[cultivo] = precio
                return precio
            
            # Si no se encuentra, usar precio por defecto
            return self.default_prices.get(cultivo, 150)
            
        except Exception as e:
            logger.error(f"Error obteniendo precio para {cultivo}: {str(e)}")
            return self.default_prices.get(cultivo, 150)
    
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
            url = f"{self.base_url}/precios-agricolas"
            
            # Headers para simular navegador
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-GT,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive',
            }
            
            # Realizar request
            async with self.client as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Parsear HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar tabla de precios
                tabla = soup.find('table', {'class': 'precios-agricolas'})
                if not tabla:
                    return None
                
                # Buscar fila del cultivo
                for fila in tabla.find_all('tr'):
                    celdas = fila.find_all('td')
                    if len(celdas) >= 3:
                        nombre = celdas[0].text.strip().lower()
                        if self._match_cultivo(cultivo, nombre):
                            # Extraer precio
                            precio_texto = celdas[2].text.strip()
                            precio = self._extract_precio(precio_texto)
                            if precio:
                                return precio
                
                return None
                
        except Exception as e:
            logger.error(f"Error consultando web MAGA: {str(e)}")
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
        # Normalizar nombres
        cultivo = cultivo.lower().strip()
        nombre = nombre.lower().strip()
        
        # Verificar coincidencia exacta
        if cultivo == nombre:
            return True
        
        # Verificar variaciones conocidas
        variaciones = CROP_VARIATIONS.get(cultivo, [])
        return nombre in variaciones
    
    def _extract_precio(self, texto: str) -> Optional[float]:
        """
        Extrae el precio de un texto
        
        Args:
            texto: Texto que contiene el precio
            
        Returns:
            Optional[float]: Precio extraído o None si no se encuentra
        """
        try:
            # Buscar patrón de precio (Q123.45 o 123.45)
            patron = r'(?:Q)?(\d+(?:\.\d{2})?)'
            match = re.search(patron, texto)
            if match:
                return float(match.group(1))
            return None
            
        except Exception:
            return None

# Instancia global
maga_api = MagaAPI()
