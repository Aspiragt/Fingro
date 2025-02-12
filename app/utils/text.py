"""
Utilidades para procesar texto con errores comunes
"""
from typing import Dict, List, Any
import re
from unidecode import unidecode
from datetime import datetime

def normalize_text(text: str) -> str:
    """
    Normaliza el texto para hacerlo más fácil de comparar
    - Convierte a minúsculas
    - Elimina acentos
    - Elimina caracteres especiales
    - Maneja errores comunes de ortografía
    """
    if not text:
        return ""
        
    # Convertir a minúsculas
    text = text.lower().strip()
    
    # Eliminar acentos
    text = unidecode(text)
    
    # Eliminar caracteres especiales
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    return text
    
def normalize_crop(text: str) -> str:
    """
    Normaliza nombres de cultivos con errores comunes
    """
    text = normalize_text(text)
    
    # Mapa de correcciones comunes
    corrections = {
        'mais': 'maiz',
        'maís': 'maiz',
        'mayz': 'maiz',
        'frijoles': 'frijol',
        'frixol': 'frijol',
        'frixoles': 'frijol',
        'frijoles': 'frijol',
        'tomates': 'tomate',
        'chile': 'chile',
        'chiles': 'chile',
        'chile pimiento': 'chile',
        'pimientos': 'chile',
        'cafe': 'cafe',
        'café': 'cafe',
        'cafeto': 'cafe',
        'cafetal': 'cafe'
    }
    
    return corrections.get(text, text)
    
def normalize_irrigation(text: str) -> str:
    """
    Normaliza tipos de riego con errores comunes
    """
    text = normalize_text(text)
    
    # Mapa de correcciones comunes
    corrections = {
        'temporal': 'temporal',
        'lluvia': 'temporal',
        'natural': 'temporal',
        'goteo': 'goteo',
        'gota': 'goteo',
        'por goteo': 'goteo',
        'aspercion': 'aspersion',
        'aspersion': 'aspersion',
        'aspersor': 'aspersion',
        'aspersores': 'aspersion',
        'otro': 'otro',
        'ninguno': 'temporal'
    }
    
    return corrections.get(text, text)
    
def normalize_commercialization(text: str) -> str:
    """Normaliza el método de comercialización"""
    text = normalize_text(text)
    
    # Mercado local
    if any(word in text for word in ['1', 'mercado', 'local', 'plaza', 'terminal']):
        return 'mercado local'
    
    # Intermediario
    if any(word in text for word in ['2', 'intermediario', 'coyote', 'comprador']):
        return 'intermediario'
    
    # Exportación
    if any(word in text for word in ['3', 'exportacion', 'exportador']):
        return 'exportacion'
    
    # Directo
    if any(word in text for word in ['4', 'directo', 'cooperativa', 'coop', 'asociacion']):
        return 'directo'
    
    return text

def normalize_yes_no(text: str) -> str:
    """
    Normaliza respuestas afirmativas/negativas con errores comunes
    """
    text = normalize_text(text)
    
    # Respuestas afirmativas
    if text in ['si', 'sí', 'simon', 'dale', 'ok', 'esta bien', 'bueno', 
               'claro', 'por supuesto', 'va', 'sale', 'asi es']:
        return 'si'
        
    # Respuestas negativas
    if text in ['no', 'nel', 'nop', 'para nada', 'nunca', 'tampoco', 
               'mejor no', 'no gracias', 'nel pastel']:
        return 'no'
        
    return text

def normalize_crop_new(crop: str) -> str:
    """
    Normaliza el nombre de un cultivo
    
    Args:
        crop: Nombre del cultivo
        
    Returns:
        str: Nombre normalizado
    """
    # Diccionario de correcciones comunes
    corrections = {
        'mais': 'maiz',
        'maís': 'maiz',
        'mayz': 'maiz',
        'frijol': 'frijol_negro',
        'frijoles': 'frijol_negro',
        'frijol negro': 'frijol_negro',
        'papa': 'papa',
        'papas': 'papa',
        'tomate': 'tomate',
        'jitomate': 'tomate'
    }
    
    # Normalizar texto
    normalized = crop.lower().strip()
    
    # Aplicar correcciones
    return corrections.get(normalized, normalized)

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza datos para logging y almacenamiento
    
    Args:
        data: Datos a sanitizar
        
    Returns:
        Dict[str, Any]: Datos sanitizados
    """
    # Campos sensibles a redactar
    sensitive_fields = {
        'phone', 'telefono', 'email', 'correo', 'address', 'direccion',
        'password', 'contraseña', 'token', 'api_key', 'secret'
    }
    
    # Patrones de datos sensibles
    patterns = {
        'phone': r'^\+?[\d\s-]{8,}$',
        'email': r'^[\w\.-]+@[\w\.-]+\.\w+$',
        'token': r'^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$'
    }
    
    def _sanitize_value(key: str, value: Any) -> Any:
        """Sanitiza un valor individual"""
        if isinstance(value, dict):
            return sanitize_data(value)
        elif isinstance(value, list):
            return [_sanitize_value(key, v) for v in value]
        elif isinstance(value, str):
            # Verificar si el campo es sensible
            key_lower = key.lower()
            if key_lower in sensitive_fields:
                return '[REDACTED]'
            
            # Verificar patrones de datos sensibles
            for pattern in patterns.values():
                if re.match(pattern, value):
                    return '[REDACTED]'
                    
        return value
    
    return {k: _sanitize_value(k, v) for k, v in data.items()}

def format_currency(amount: float, currency: str = 'GTQ') -> str:
    """
    Formatea un monto como moneda
    
    Args:
        amount: Monto a formatear
        currency: Código de moneda (default: GTQ)
        
    Returns:
        str: Monto formateado
    """
    return f"{currency} {amount:,.2f}"

def format_date(date: datetime, format: str = '%Y-%m-%d') -> str:
    """
    Formatea una fecha
    
    Args:
        date: Fecha a formatear
        format: Formato deseado
        
    Returns:
        str: Fecha formateada
    """
    return date.strftime(format)
