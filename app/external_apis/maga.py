"""
Módulo para obtener información de precios y datos históricos del MAGA
"""
import logging
from typing import Dict, Any, Optional, List, Union
import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime, timedelta
import re
from cachetools import TTLCache
from pydantic import BaseModel, Field
from app.config import settings
from app.utils.constants import CROP_VARIATIONS

logger = logging.getLogger(__name__)

class DatosCultivo(BaseModel):
    """Modelo de datos de un cultivo"""
    rendimiento_promedio: float = Field(..., description="Rendimiento promedio en quintales por hectárea")
    costos_fijos: float = Field(..., description="Costos fijos por hectárea")
    costos_variables: float = Field(..., description="Costos variables por hectárea")
    riesgo_mercado: float = Field(..., ge=0, le=1, description="Factor de riesgo de mercado (0-1)")
    ciclo_cultivo: int = Field(..., description="Duración del ciclo en meses")

class MagaAPI:
    """Cliente para obtener información de precios y datos históricos del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA API"""
        self.base_url = settings.MAGA_BASE_URL
        
        # Intentar usar HTTP/2 si está disponible
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                http2=True,
                timeout=30.0
            )
        except ImportError:
            # Si no está disponible HTTP/2, usar HTTP/1.1
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                http2=False,
                timeout=30.0
            )
        
        self.ua = UserAgent()
        
        # Caché de precios con TTL de 6 horas
        self.price_cache = TTLCache(maxsize=100, ttl=21600)
        
        # Caché de datos históricos con TTL de 24 horas
        self.history_cache = TTLCache(maxsize=100, ttl=86400)
        
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
        
        # Datos históricos por defecto
        self.default_history = {
            'maiz': DatosCultivo(
                rendimiento_promedio=80,
                costos_fijos=3000,
                costos_variables=5000,
                riesgo_mercado=0.2,
                ciclo_cultivo=4
            ),
            'frijol': DatosCultivo(
                rendimiento_promedio=30,
                costos_fijos=2500,
                costos_variables=4000,
                riesgo_mercado=0.15,
                ciclo_cultivo=3
            ),
            'papa': DatosCultivo(
                rendimiento_promedio=250,
                costos_fijos=5000,
                costos_variables=8000,
                riesgo_mercado=0.25,
                ciclo_cultivo=4
            ),
            'tomate': DatosCultivo(
                rendimiento_promedio=2000,
                costos_fijos=8000,
                costos_variables=15000,
                riesgo_mercado=0.3,
                ciclo_cultivo=4
            ),
            'chile': DatosCultivo(
                rendimiento_promedio=1500,
                costos_fijos=7000,
                costos_variables=12000,
                riesgo_mercado=0.25,
                ciclo_cultivo=5
            )
        }
    
    async def get_precio_cultivo(self, cultivo: str) -> float:
        """
        Obtiene el precio actual de un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            float: Precio en quetzales por quintal
        """
        try:
            # Normalizar nombre del cultivo
            cultivo = cultivo.lower().strip()
            
            # Buscar en caché primero
            if cultivo in self.price_cache:
                return self.price_cache[cultivo]
                
            # Intentar obtener precio de la web
            try:
                precio = await self._fetch_precio_web(cultivo)
                if precio:
                    self.price_cache[cultivo] = precio
                    return precio
            except Exception as e:
                logger.error(f"Error en _fetch_precio_web para {cultivo}: {str(e)}")
                
            # Si no se pudo obtener, usar precio por defecto
            default_price = self.default_prices.get(cultivo, 200)
            logger.info(f"Usando precio por defecto para {cultivo}: Q{default_price}")
            return default_price
            
        except Exception as e:
            logger.error(f"Error obteniendo precio para {cultivo}: {str(e)}")
            return self.default_prices.get(cultivo, 200)

    async def get_datos_historicos(self, cultivo: str) -> Dict[str, Any]:
        """
        Obtiene datos históricos de un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            Dict[str, Any]: Datos históricos del cultivo
        """
        try:
            # Normalizar nombre del cultivo
            cultivo = cultivo.lower().strip()
            
            # Buscar en caché primero
            if cultivo in self.history_cache:
                return self.history_cache[cultivo]
                
            # Intentar obtener datos de la web
            try:
                datos = await self._fetch_datos_web(cultivo)
                if datos:
                    self.history_cache[cultivo] = datos
                    return datos
            except Exception as e:
                logger.error(f"Error en _fetch_datos_web para {cultivo}: {str(e)}")
                
            # Si no se pudo obtener, usar datos por defecto
            default_data = self.default_history.get(cultivo)
            if default_data:
                logger.info(f"Usando datos históricos por defecto para {cultivo}")
                return default_data.dict()
            else:
                # Si no hay datos por defecto, usar datos genéricos
                logger.info(f"Usando datos históricos genéricos para {cultivo}")
                return DatosCultivo(
                    rendimiento_promedio=50,
                    costos_fijos=3000,
                    costos_variables=5000,
                    riesgo_mercado=0.2,
                    ciclo_cultivo=4
                ).dict()
                
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos para {cultivo}: {str(e)}")
            return DatosCultivo(
                rendimiento_promedio=50,
                costos_fijos=3000,
                costos_variables=5000,
                riesgo_mercado=0.2,
                ciclo_cultivo=4
            ).dict()
    
    async def _fetch_precio_web(self, cultivo: str) -> Optional[float]:
        """
        Obtiene el precio de un cultivo desde la web del MAGA
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            Optional[float]: Precio en quetzales por quintal si se encuentra
        """
        try:
            # Construir URL
            url = f"{self.base_url}/precios"
            
            # Headers para simular navegador
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html',
                'Accept-Language': 'es-GT,es',
                'Connection': 'keep-alive'
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
    
    async def _fetch_datos_web(self, cultivo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos históricos de un cultivo desde la web del MAGA
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            Optional[Dict[str, Any]]: Datos históricos del cultivo si se encuentran
        """
        try:
            # Construir URL
            url = f"{self.base_url}/estadisticas/{cultivo}"
            
            # Headers para simular navegador
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html',
                'Accept-Language': 'es-GT,es',
                'Connection': 'keep-alive'
            }
            
            # Realizar request
            async with self.client as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # TODO: Implementar parseo de datos históricos
                return None
            
        except Exception as e:
            logger.error(f"Error en _fetch_datos_web para {cultivo}: {str(e)}")
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
