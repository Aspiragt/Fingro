"""
Utilidades para procesar texto con errores comunes
"""
from typing import Dict, List
import re
from unidecode import unidecode

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

"""
Utilidades para manejo de texto
"""
import unicodedata
import re
from typing import Optional, Tuple

def normalize_text_new(text: str) -> str:
    """
    Normaliza texto para búsquedas flexibles:
    - Quita acentos
    - Convierte a minúsculas
    - Quita espacios extra
    - Quita caracteres especiales
    
    Args:
        text: Texto a normalizar
        
    Returns:
        str: Texto normalizado
        
    Examples:
        >>> normalize_text_new("Maíz")
        'maiz'
        >>> normalize_text_new("café oro")  
        'cafe oro'
        >>> normalize_text_new("FRÍJOL NEGRO")
        'frijol negro'
    """
    if not text:
        return ""
        
    # Convertir a minúsculas
    text = text.lower()
    
    # Quitar acentos
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Normalizar caracteres especiales comunes
    replacements = {
        'ñ': 'n',
        'ü': 'u',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Quitar caracteres especiales y espacios extra
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = ' '.join(text.split())
    
    return text

def parse_area(text: str) -> Optional[Tuple[float, str]]:
    """
    Parsea un texto que representa un área y devuelve el valor y la unidad
    
    Args:
        text: Texto a parsear (ej: "2.5 manzanas", "3 ha", "1,000 mz")
        
    Returns:
        Tuple[float, str]: (valor, unidad) o None si no se puede parsear
        
    Examples:
        >>> parse_area("2.5 manzanas")
        (2.5, 'manzana')
        >>> parse_area("3 ha")
        (3.0, 'hectarea')
        >>> parse_area("1,000 mz")
        (1000.0, 'manzana')
    """
    try:
        # Quitar espacios extra y convertir a minúsculas
        text = text.lower().strip()
        
        # Quitar comas de números grandes
        text = text.replace(',', '')
        
        # Permitir punto o coma decimal
        text = text.replace(';', '.')
        
        # Extraer número y unidad
        match = re.match(r'^([\d.]+)\s*([a-zA-Z]+)$', text)
        if not match:
            return None
            
        value, unit = match.groups()
        
        # Convertir valor a float
        value = float(value)
        
        # Normalizar unidad
        unit_map = {
            'mz': 'manzana',
            'manzana': 'manzana',
            'manzanas': 'manzana',
            'ha': 'hectarea',
            'has': 'hectarea',
            'hectarea': 'hectarea',
            'hectareas': 'hectarea',
            'hectárea': 'hectarea',
            'hectáreas': 'hectarea'
        }
        
        unit = unit_map.get(unit)
        if not unit:
            return None
            
        return (value, unit)
        
    except Exception as e:
        return None

def format_number(number: float, decimals: int = 0) -> str:
    """
    Formatea un número con separadores de miles y decimales
    
    Args:
        number: Número a formatear
        decimals: Número de decimales a mostrar
        
    Returns:
        str: Número formateado
        
    Examples:
        >>> format_number(1234.56)
        '1,235'
        >>> format_number(1234.56, 2)
        '1,234.56'
    """
    return f"{number:,.{decimals}f}"

def get_crop_variations(crop: str) -> set:
    """
    Genera variaciones comunes de nombres de cultivos
    
    Args:
        crop: Nombre del cultivo
        
    Returns:
        set: Conjunto de variaciones del nombre
        
    Examples:
        >>> get_crop_variations("maiz")
        {'maiz', 'maíz', 'mais', 'máiz', 'máis'}
    """
    variations = {crop}
    
    # Mapa de variaciones comunes
    variation_map = {
        'maiz': {'mais', 'máiz', 'máis'},
        'cafe': {'café'},
        'frijol': {'fríjol', 'frejol', 'fréjol', 'frijoles'},
        'platano': {'plátano', 'platanos', 'plátanos'},
        'limon': {'limón', 'limones'},
        'brocoli': {'brócoli', 'brocolis', 'brócolis'},
    }
    
    normalized = normalize_text_new(crop)
    if normalized in variation_map:
        variations.update(variation_map[normalized])
    
    return variations

def parse_yes_no(text: str) -> Optional[bool]:
    """
    Parsea una respuesta sí/no
    
    Args:
        text: Texto a parsear
        
    Returns:
        bool: True para sí, False para no, None si no es válido
        
    Examples:
        >>> parse_yes_no("si")
        True
        >>> parse_yes_no("No")
        False
        >>> parse_yes_no("tal vez")
        None
    """
    if not text:
        return None
        
    # Normalizar texto
    text = normalize_text(text)
    
    # Respuestas válidas
    yes_responses = {
        'si', 's', 'sí', 'yes', 'y', 
        'dale', 'va', 'bueno', 'ok',
        'claro', 'por supuesto'
    }
    
    no_responses = {
        'no', 'n', 'nop', 'nel', 
        'mejor no', 'paso', 'negativo'
    }
    
    if text in yes_responses:
        return True
    elif text in no_responses:
        return False
    else:
        return None

def parse_channel(text: str) -> Optional[str]:
    """
    Parsea un canal de comercialización
    
    Args:
        text: Texto a parsear
        
    Returns:
        str: Canal normalizado o None si no es válido
        
    Examples:
        >>> parse_channel("1")
        'mercado_local'
        >>> parse_channel("cooperativa")
        'cooperativa'
        >>> parse_channel("mayorista")
        'mayorista'
    """
    if not text:
        return None
        
    # Normalizar texto
    text = normalize_text(text)
    
    # Mapeo de respuestas válidas
    channel_map = {
        # Por número
        '1': 'mercado_local',
        '2': 'mayorista',
        '3': 'cooperativa',
        '4': 'exportacion',
        
        # Por texto
        'mercado': 'mercado_local',
        'mercado local': 'mercado_local',
        'local': 'mercado_local',
        'plaza': 'mercado_local',
        
        'mayorista': 'mayorista',
        'mayoreo': 'mayorista',
        'distribuidor': 'mayorista',
        
        'cooperativa': 'cooperativa',
        'coop': 'cooperativa',
        'asociacion': 'cooperativa',
        
        'exportacion': 'exportacion',
        'exportación': 'exportacion',
        'export': 'exportacion',
        'internacional': 'exportacion'
    }
    
    return channel_map.get(text)
