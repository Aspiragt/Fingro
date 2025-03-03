"""
Definición de canales de comercialización
"""
from enum import Enum, auto

class CanalComercializacion(str, Enum):
    """Canales de comercialización disponibles"""
    MAYORISTA = "mayorista"
    COOPERATIVA = "cooperativa"
    EXPORTACION = "exportacion"
    MERCADO_LOCAL = "mercado_local"
    
    def __str__(self) -> str:
        return self.value
