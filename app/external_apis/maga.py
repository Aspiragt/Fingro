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
        # Cargar precios del JSON
        try:
            import os
            json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'maga_data.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                import json
                self.maga_prices = json.load(f)
        except Exception as e:
            logger.error(f"Error cargando precios de MAGA: {str(e)}")
            self.maga_prices = []
        
        # Datos históricos por defecto (como fallback)
        self.default_prices = {
            'maiz': 150,
            'frijol': 500,
            'cafe': 1000,
            'tomate': 200,
            'chile': 300,
            'papa': 250,
            'cebolla': 280,
            'repollo': 150,
            'arveja': 400,
            'aguacate': 450,
            'platano': 200,
            'limon': 300,
            'zanahoria': 200,
            'brocoli': 250,
            'yuca': 150,
            'rabano': 200,
            'lechuga': 180,
            'pepino': 220,
            'sandia': 300,
            'melon': 350,
            'camote': 180
        }
        
        # Factores de ajuste por canal de comercialización
        self.price_adjustments = {
            # Los precios base son mayoristas
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
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza el texto para comparación"""
        import unicodedata
        # Normalizar NFD y eliminar diacríticos
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        # A minúsculas y remover espacios extra
        return text.lower().strip()
    
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
            dict: Diccionario con precio, medida y canal
        """
        try:
            # Normalizar nombre
            cultivo = self._normalize_text(cultivo)
            
            # Buscar precio en datos de MAGA
            base_price = None
            medida = 'Quintal'  # Por defecto usar quintales
            mercado = 'Nacional'
            
            for precio in self.maga_prices:
                producto = self._normalize_text(precio['Producto'])
                if cultivo in producto:
                    base_price = precio['Precio']
                    medida = precio['Medida']
                    mercado = precio['Mercado']
                    break
            
            # Si no encontramos precio, usar el default
            if base_price is None:
                logger.warning(f"Usando precio por defecto para {cultivo}")
                base_price = self.default_prices.get(cultivo)
                if base_price is None:
                    logger.error(f"No se encontró precio para {cultivo}")
                    return None
            
            # Si se especifica un canal, devolver solo ese precio
            if canal:
                precio_ajustado = self._adjust_price(base_price, cultivo, canal)
                return {
                    'precio': precio_ajustado,
                    'medida': medida,
                    'canal': canal,
                    'mercado': mercado
                }
            
            # Si no se especifica canal, devolver todos los precios recomendados
            precios = {}
            for canal in self._get_recommended_channels(cultivo):
                precio_ajustado = self._adjust_price(base_price, cultivo, canal)
                precios[canal] = {
                    'precio': precio_ajustado,
                    'medida': medida,
                    'canal': canal,
                    'mercado': mercado
                }
            
            # Devolver el precio del mejor canal
            mejor_canal = list(precios.keys())[0]
            return precios[mejor_canal]
            
        except Exception as e:
            logger.error(f"Error obteniendo precio para {cultivo}: {str(e)}")
            return None

# Instancia global
maga_api = MagaAPI()
