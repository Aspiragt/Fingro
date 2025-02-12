"""
Módulo para obtener información de precios y datos históricos del MAGA usando datos abiertos
"""
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import httpx
import json
from datetime import datetime, timedelta
import re
from cachetools import TTLCache
from pydantic import BaseModel, Field
import zipfile
import io
import os
from difflib import get_close_matches
from app.config import settings

logger = logging.getLogger(__name__)

class DatosCultivo(BaseModel):
    """Modelo de datos de un cultivo"""
    rendimiento_promedio: float = Field(..., description="Rendimiento promedio en quintales por hectárea")
    costos_fijos: float = Field(..., description="Costos fijos por hectárea")
    costos_variables: float = Field(..., description="Costos variables por hectárea")
    riesgo_mercado: float = Field(..., ge=0, le=1, description="Factor de riesgo de mercado (0-1)")
    ciclo_cultivo: int = Field(..., description="Duración del ciclo en meses")

class PrecioMaga(BaseModel):
    """Modelo para los precios del MAGA"""
    Actor: str
    Periodicidad: str
    Mercado: str
    Producto: str
    Medida: str
    Fecha: str
    Moneda: str
    Precio: Optional[float] = None

class CanalComercializacion:
    """Tipos de canales de comercialización"""
    MAYORISTA = 'mayorista'
    COOPERATIVA = 'cooperativa'
    EXPORTACION = 'exportacion'
    MERCADO_LOCAL = 'mercado_local'

class MagaAPI:
    """Cliente para obtener información de precios y datos históricos del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA API"""
        self.base_url = "https://precios.maga.gob.gt/archivos/datos-abiertos"
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Caché de precios con TTL de 6 horas
        self.price_cache = TTLCache(maxsize=100, ttl=21600)
        
        # Datos históricos por defecto
        self.default_prices = {
            'maiz': 150,
            'frijol': 500,
            'cafe': 1000,
            'tomate': 200,
            'chile': 300,
            'papa': 250,
            'cebolla': 280,
            'repollo': 150,
            'arveja': 400
        }
        
        # Factores de ajuste por canal de comercialización
        self.price_adjustments = {
            # Los precios MAGA son mayoristas
            CanalComercializacion.MAYORISTA: 1.0,
            
            # Cooperativas suelen tener mejores precios (10% más)
            CanalComercializacion.COOPERATIVA: 1.1,
            
            # Exportación tiene los mejores precios (30% más)
            CanalComercializacion.EXPORTACION: 1.3,
            
            # Mercado local suele tener precios más bajos (-20%)
            CanalComercializacion.MERCADO_LOCAL: 0.8
        }
        
        # Cultivos que típicamente se exportan
        self.export_crops = {
            'cafe', 'arveja', 'aguacate', 'platano', 'limon'
        }
        
        # Cultivos que típicamente se venden a cooperativas
        self.cooperative_crops = {
            'cafe', 'maiz', 'frijol', 'papa'
        }
        
        # Mapeo de cultivos a sus nombres en MAGA
        self.crop_mapping = {
            'tomate': 'Tomate de cocina, mediano, de primera',
            'papa': 'Papa Loman, lavada, mediana, de primera',
            'maiz': 'Maíz blanco, de primera',
            'frijol': 'Frijol negro, de primera',
            'cafe': 'Cacao (Despulpado), seco, de primera',  # No hay café, usamos cacao
            'chile': 'Chile Pimiento, mediano, de primera',
            'cebolla': 'Cebolla seca, blanca, mediana, de primera',
            'repollo': 'Repollo blanco, mediano, de primera',
            'arveja': 'Arveja china, revuelta, de primera'
        }
        
        # Mercados disponibles
        self.available_markets = ['La Terminal', 'CENMA', '21 Calle']
        self.default_market = 'La Terminal'  # Mercado principal
        
        # Cargar datos al iniciar
        self._load_latest_data()
    
    def _get_latest_data_url(self) -> str:
        """Obtiene la URL del archivo JSON más reciente"""
        current_date = datetime.now()
        month_names = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        # Intentar con el mes actual
        month_name = month_names[current_date.month]
        url = f"{self.base_url}/Precios%20mensuales%20de%20diversos%20productos%20agr%C3%ADcolas%20en%20Guatemala%20a%20{month_name}%20{current_date.year}%20JSON.zip"
        
        # Si no existe, intentar con el mes anterior
        if not self._url_exists(url):
            current_date = current_date.replace(day=1) - timedelta(days=1)
            month_name = month_names[current_date.month]
            url = f"{self.base_url}/Precios%20mensuales%20de%20diversos%20productos%20agr%C3%ADcolas%20en%20Guatemala%20a%20{month_name}%20{current_date.year}%20JSON.zip"
            
        return url
    
    def _url_exists(self, url: str) -> bool:
        """Verifica si una URL existe"""
        try:
            response = httpx.head(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error verificando URL {url}: {str(e)}")
            return False
    
    def _load_latest_data(self):
        """Carga los datos más recientes del MAGA"""
        try:
            # Obtener URL del archivo más reciente
            url = self._get_latest_data_url()
            logger.info(f"Intentando descargar datos de: {url}")
            
            # Descargar archivo ZIP
            response = httpx.get(url)
            if response.status_code != 200:
                logger.error(f"Error descargando datos: {response.status_code}")
                self.latest_data = None
                return
            
            # Extraer JSON del ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                json_files = [f for f in z.namelist() if f.endswith('.json')]
                if not json_files:
                    logger.error("No se encontraron archivos JSON en el ZIP")
                    self.latest_data = None
                    return
                
                # Leer primer archivo JSON
                with z.open(json_files[0]) as f:
                    data = json.load(f)
                    
                # Convertir a modelos y filtrar precios nulos
                self.latest_data = [
                    PrecioMaga(**item) 
                    for item in data 
                    if item.get('Precio') is not None
                ]
                
                # Crear lista de productos disponibles
                self.available_products = sorted(list(set(
                    item.Producto for item in self.latest_data
                    if item.Mercado == self.default_market
                )))
                    
            logger.info("Datos MAGA cargados exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando datos MAGA: {str(e)}")
            self.latest_data = None
            self.available_products = []
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza un texto para búsqueda"""
        # Convertir a minúsculas y quitar espacios
        text = text.lower().strip()
        
        # Quitar tildes
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Quitar palabras comunes y calificadores
        common_words = {
            'de', 'del', 'la', 'las', 'los', 'el', 'y', 'con', 'sin',
            'primera', 'segunda', 'tercera', 'mediano', 'mediana',
            'grande', 'pequeño', 'pequeña', 'importado', 'nacional',
            'seco', 'seca', 'fresco', 'fresca'
        }
        words = text.split()
        words = [w for w in words if w not in common_words]
        
        return ' '.join(words)
    
    def _find_similar_product(self, query: str) -> Tuple[str, float]:
        """
        Encuentra el producto más similar al consultado
        
        Args:
            query: Nombre del producto a buscar
            
        Returns:
            Tuple[str, float]: (Nombre del producto más similar, porcentaje de similitud)
        """
        # Normalizar búsqueda
        query = self._normalize_text(query)
        logger.info(f"Buscando producto similar a: {query}")
        
        # Preparar lista de productos normalizados
        products_norm = {
            self._normalize_text(p): p 
            for p in self.available_products
        }
        logger.info(f"Productos disponibles: {list(products_norm.keys())[:5]}...")
        
        # Buscar coincidencias
        matches = get_close_matches(query, products_norm.keys(), n=1, cutoff=0.2)
        
        if matches:
            similarity = sum(1 for a, b in zip(query, matches[0]) if a == b) / max(len(query), len(matches[0]))
            logger.info(f"Coincidencia encontrada: {matches[0]} (similitud: {similarity:.2%})")
            return products_norm[matches[0]], similarity
        
        logger.info("No se encontraron coincidencias")
        return None, 0.0
    
    def _get_recommended_channels(self, cultivo: str) -> list:
        """
        Obtiene los canales de comercialización recomendados para un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            list: Lista de canales recomendados ordenados por prioridad
        """
        channels = []
        
        # Verificar si es cultivo de exportación
        if cultivo in self.export_crops:
            channels.append(CanalComercializacion.EXPORTACION)
            
        # Verificar si se vende a cooperativas
        if cultivo in self.cooperative_crops:
            channels.append(CanalComercializacion.COOPERATIVA)
            
        # Agregar canales por defecto
        channels.extend([
            CanalComercializacion.MAYORISTA,
            CanalComercializacion.MERCADO_LOCAL
        ])
        
        return channels
    
    def _adjust_price(self, price: float, cultivo: str, canal: str) -> float:
        """
        Ajusta el precio según el canal de comercialización
        
        Args:
            price: Precio base
            cultivo: Nombre del cultivo
            canal: Canal de comercialización
            
        Returns:
            float: Precio ajustado
        """
        # Obtener factor de ajuste
        factor = self.price_adjustments.get(canal, 1.0)
        
        # Ajustar precio
        adjusted_price = price * factor
        
        # Redondear a 2 decimales
        return round(adjusted_price, 2)
    
    async def get_precio_cultivo(self, cultivo: str, canal: str = None) -> dict:
        """
        Obtiene el precio actual de un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            canal: Canal de comercialización (opcional)
            
        Returns:
            dict: Diccionario con precios por canal
        """
        try:
            # Normalizar nombre
            cultivo = cultivo.lower().strip()
            
            # Obtener precio base
            base_price = None
            
            # Verificar caché
            if cultivo in self.price_cache:
                base_price = self.price_cache[cultivo]
            else:
                # Obtener nombre completo
                crop_full_name = self.crop_mapping.get(cultivo)
                
                # Si no está en el mapeo, buscar producto similar
                if not crop_full_name and self.latest_data:
                    similar_product, similarity = self._find_similar_product(cultivo)
                    if similar_product and similarity > 0.25:
                        logger.info(f"Usando producto similar: {similar_product} (similitud: {similarity:.2%})")
                        crop_full_name = similar_product
                
                if not crop_full_name:
                    logger.warning(f"Cultivo no encontrado en mapeo MAGA: {cultivo}")
                    base_price = self.default_prices.get(cultivo, 150.0)
                else:
                    # Buscar en datos más recientes
                    if self.latest_data:
                        matches = [
                            item for item in self.latest_data 
                            if item.Producto == crop_full_name and
                            item.Mercado == self.default_market and
                            item.Precio is not None
                        ]
                        
                        if matches:
                            # Ordenar por fecha y tomar el más reciente
                            latest = sorted(matches, key=lambda x: x.Fecha)[-1]
                            base_price = latest.Precio
                            self.price_cache[cultivo] = base_price
            
            if base_price is None:
                base_price = self.default_prices.get(cultivo, 150.0)
            
            # Si se especifica un canal, devolver solo ese precio
            if canal:
                return {
                    'precio': self._adjust_price(base_price, cultivo, canal),
                    'canal': canal
                }
            
            # Obtener canales recomendados
            channels = self._get_recommended_channels(cultivo)
            
            # Calcular precios para cada canal
            prices = {
                channel: self._adjust_price(base_price, cultivo, channel)
                for channel in channels
            }
            
            return {
                'precios': prices,
                'canales_recomendados': channels
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo precio para {cultivo}: {str(e)}")
            return {
                'precios': {
                    CanalComercializacion.MAYORISTA: self.default_prices.get(cultivo, 150.0)
                },
                'canales_recomendados': [CanalComercializacion.MAYORISTA]
            }

# Instancia global
maga_api = MagaAPI()
