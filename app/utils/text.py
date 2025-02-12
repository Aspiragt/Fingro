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
    """
    Normaliza métodos de comercialización con errores comunes
    """
    text = normalize_text(text)
    
    # Mapa de correcciones comunes
    corrections = {
        'local': 'mercado local',
        'mercado': 'mercado local',
        'pueblo': 'mercado local',
        'intermediario': 'intermediario',
        'coyote': 'intermediario',
        'revendedor': 'intermediario',
        'exportacion': 'exportacion',
        'exportar': 'exportacion',
        'extranjero': 'exportacion',
        'directo': 'directo',
        'propio': 'directo',
        'personal': 'directo'
    }
    
    return corrections.get(text, text)
    
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
