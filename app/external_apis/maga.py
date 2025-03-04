"""
Módulo para interactuar con la API del Ministerio de Agricultura, 
Ganadería y Alimentación (MAGA) de Guatemala

Este módulo obtiene información sobre precios de mercado, 
recomendaciones técnicas y alertas climáticas.
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MagaAPI:
    """
    Cliente para el API del MAGA
    
    Por el momento usa datos locales simulados, pero en el futuro
    podría conectarse a una API real del MAGA.
    """
    
    def __init__(self):
        """Inicializa el cliente de la API del MAGA"""
        # Cargar datos de precios simulados
        self.precios_data = self._load_data("precios")
        self.rendimientos_data = self._load_data("rendimientos")
    
    def _load_data(self, data_type: str) -> Dict[str, Any]:
        """
        Carga datos locales simulados
        
        Args:
            data_type: Tipo de datos a cargar ('precios', 'rendimientos')
            
        Returns:
            Diccionario con los datos
        """
        try:
            # Ubicación relativa del archivo de datos
            base_dir = Path(__file__).parent
            data_file = base_dir / "data" / f"{data_type}_simulados.json"
            
            if not data_file.exists():
                logger.warning(f"Archivo de datos {data_file} no encontrado. Usando datos por defecto.")
                return {}
                
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar datos {data_type}: {e}")
            return {}
    
    def get_precio_mercado(self, cultivo: str, departamento: str = None) -> Dict[str, Any]:
        """
        Obtiene precios actuales del mercado para un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            departamento: Departamento de Guatemala (opcional)
            
        Returns:
            Diccionario con precios por mercados
        """
        cultivo = cultivo.lower()
        
        if cultivo not in self.precios_data:
            # Devolver estructura por defecto para cultivos no encontrados
            return {
                "local": 120,  # Quetzales por quintal
                "mayorista": 140,
                "exportacion": 160,
                "fuente": "Estimado FinGro",
                "fecha_actualizacion": "2025-03-01"
            }
        
        return self.precios_data.get(cultivo, {})
    
    def get_rendimiento(self, cultivo: str, departamento: str = None) -> Dict[str, Any]:
        """
        Obtiene información de rendimiento histórico para un cultivo
        
        Args:
            cultivo: Nombre del cultivo
            departamento: Departamento de Guatemala (opcional)
            
        Returns:
            Diccionario con datos de rendimiento
        """
        cultivo = cultivo.lower()
        
        if cultivo not in self.rendimientos_data:
            # Rendimiento por defecto
            return {
                "quintales_por_hectarea": 50,
                "variacion_anual": 0.05,  # 5% de variación anual
                "fuente": "Estimado FinGro",
                "fecha_actualizacion": "2025-03-01"
            }
        
        return self.rendimientos_data.get(cultivo, {})
    
    def get_datos_cultivo(self, cultivo: str) -> Dict[str, Any]:
        """
        Obtiene datos generales para un cultivo (precio, rendimiento, costos)
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            Diccionario con datos del cultivo
        """
        cultivo = cultivo.lower()
        
        # Obtener precio y rendimiento
        precios = self.get_precio_mercado(cultivo)
        rendimiento = self.get_rendimiento(cultivo)
        
        # Datos por defecto para cualquier cultivo
        return {
            "nombre": cultivo.capitalize(),
            "rendimiento_promedio": rendimiento.get("quintales_por_hectarea", 50),
            "precio_quintal": precios.get("mayorista", 150),
            "costo_por_hectarea": 8000,  # Costo estimado en quetzales
            "tiempo_cultivo": 120,  # Días promedio
            "riesgo_mercado": 0.1,  # 10% riesgo de mercado
        }
    
    async def get_datos_historicos(self, cultivo: str) -> Dict[str, Any]:
        """
        Obtiene datos históricos para un cultivo (asíncrono para compatibilidad)
        
        Args:
            cultivo: Nombre del cultivo
            
        Returns:
            Diccionario con datos históricos
        """
        return self.get_datos_cultivo(cultivo)

# Instancia global
maga_api = MagaAPI()
