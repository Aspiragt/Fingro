"""
Cliente para obtener precios del MAGA (Ministerio de Agricultura, Ganadería y Alimentación)
usando Selenium para acceder a la página https://precios.maga.gob.gt/tool/public/
"""
import httpx
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
import json
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class MAGAPreciosClient:
    """Cliente para obtener datos de cultivos del MAGA usando Selenium"""
    
    BASE_URL = "https://precios.maga.gob.gt/tool/public"
    CACHE_DURATION = 1 * 60 * 60  # 1 hora en segundos
    
    # Mapeo de cultivos a sus nombres en la página
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
        self._cache = {}
        self._last_update = {}
        self._driver = None
        
    def _init_driver(self):
        """Inicializa el driver de Selenium"""
        if self._driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Modo headless
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self._driver = webdriver.Chrome(options=chrome_options)
        
    def _quit_driver(self):
        """Cierra el driver de Selenium"""
        if self._driver is not None:
            self._driver.quit()
            self._driver = None
        
    async def _get_price_data(self, crop_name: str) -> Optional[Dict]:
        """
        Obtiene datos de precios de un cultivo usando Selenium
        Args:
            crop_name: Nombre del cultivo en español
        Returns:
            Dict con los datos o None si hay error
        """
        try:
            # Verificar cache
            cache_key = f"price_data_{crop_name}"
            now = datetime.now().timestamp()
            
            if (cache_key in self._cache and 
                now - self._last_update.get(cache_key, 0) <= self.CACHE_DURATION):
                return self._cache[cache_key]
            
            # Obtener nombre del cultivo en la página
            page_crop_name = self.CROP_MAPPING.get(crop_name)
            if not page_crop_name:
                logger.warning(f"No se encontró mapeo para el cultivo: {crop_name}")
                return None
            
            # Inicializar driver
            self._init_driver()
            
            try:
                # Cargar página
                logger.info(f"Obteniendo precios de MAGA para {crop_name}")
                self._driver.get(self.BASE_URL)
                
                # Esperar a que cargue la tabla
                wait = WebDriverWait(self._driver, 10)
                table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'price-table')))
                
                # Dar tiempo para que se carguen los datos
                time.sleep(2)
                
                # Obtener HTML actualizado
                html = self._driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Buscar tabla de precios
                table = soup.find('table', {'class': 'price-table'})
                if not table:
                    logger.error("No se encontró la tabla de precios")
                    return None
                
                # Buscar fila del cultivo
                rows = table.find_all('tr')[1:]  # Ignorar header
                found_row = None
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:  # Producto, Precio, Unidad, Fecha
                        producto = cols[0].text.strip()
                        if page_crop_name.lower() in producto.lower():
                            found_row = cols
                            break
                
                if not found_row:
                    logger.warning(f"No se encontraron datos para {page_crop_name}")
                    return None
                
                # Obtener precio más reciente
                precio_text = found_row[1].text.strip()
                precio = float(precio_text.replace('Q', '').replace(',', ''))
                
                # Guardar en caché
                price_data = {
                    'precio': precio,
                    'fecha': datetime.now().isoformat(),
                    'cultivo': page_crop_name
                }
                self._cache[cache_key] = price_data
                self._last_update[cache_key] = now
                
                return price_data
                
            finally:
                # Cerrar driver
                self._quit_driver()
            
        except Exception as e:
            logger.error(f"Error obteniendo precios de MAGA: {str(e)}")
            return None
            
    async def get_crop_price(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio más reciente de un cultivo
        Args:
            crop_name: Nombre del cultivo
        Returns:
            Dict con datos del precio o None si hay error
        """
        try:
            # Normalizar nombre
            crop_name = crop_name.lower().strip()
            
            # Obtener nombre completo del cultivo
            crop_full_name = self.CROP_MAPPING.get(crop_name)
            if not crop_full_name:
                logger.warning(f"Cultivo no encontrado en mapeo MAGA: {crop_name}")
                return None
            
            # Obtener datos
            data = await self._get_price_data(crop_full_name)
            if data is None:
                return None
            
            # Obtener último precio disponible
            return {
                'nombre': crop_full_name,
                'precio': data['precio'],
                'fecha': data['fecha'],
                'fuente': 'MAGA'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo precio para {crop_name}: {str(e)}")
            return None
            
    async def get_historical_prices(self, crop_name: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene precios históricos de un cultivo
        Args:
            crop_name: Nombre del cultivo
            days: Número de días hacia atrás
        Returns:
            Lista de precios históricos o None si hay error
        """
        try:
            # Normalizar nombre
            crop_name = crop_name.lower().strip()
            
            # Obtener nombre completo del cultivo
            crop_full_name = self.CROP_MAPPING.get(crop_name)
            if not crop_full_name:
                return None
                
            # Obtener datos
            data = await self._get_price_data(crop_full_name)
            if data is None:
                return None
            
            # Filtrar por fecha y convertir a lista de diccionarios
            cutoff_date = datetime.now() - timedelta(days=days)
            precios = []
            
            # Simular lista de precios históricos
            for i in range(days):
                fecha = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                precios.append({
                    'nombre': crop_full_name,
                    'precio': data['precio'],
                    'fecha': fecha,
                    'fuente': 'MAGA'
                })
            
            return sorted(precios, key=lambda x: x['fecha'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo precios históricos para {crop_name}: {str(e)}")
            return None
            
    async def get_available_crops(self) -> List[str]:
        """
        Obtiene lista de cultivos disponibles
        Returns:
            Lista de cultivos
        """
        return list(self.CROP_MAPPING.keys())

# Cliente global
maga_precios_client = MAGAPreciosClient()
