from typing import List, Optional, Any
import re
from unidecode import unidecode
from thefuzz import fuzz
import Levenshtein
from datetime import datetime

# Diccionarios de variaciones
SPELLING_VARIATIONS = {
    # Cultivos
    'maíz': ['mais', 'maís', 'mayz', 'mais', 'maiz'],
    'frijol': ['frijoles', 'frixol', 'frixoles', 'frijoles'],
    'café': ['cafe', 'cafee', 'kafe', 'cafeto'],
    'cardamomo': ['cardamono', 'cardamome', 'cardamon'],
    
    # Unidades de Área
    'manzana': ['mansana', 'manzanas', 'mansanas', 'manzna'],
    'hectárea': ['hectarea', 'ectarea', 'hetarea', 'hectaria'],
    'cuerda': ['cuerda', 'querda', 'kuerda'],
    
    # Sistemas de Riego
    'goteo': ['gotero', 'goteos', 'gotear'],
    'aspersión': ['aspercion', 'aspersion', 'aspersor'],
    'lluvia': ['yuvia', 'luvia', 'yuvias'],
    
    # Monedas
    'quetzales': ['quetzal', 'quetsales', 'ketzales', 'Q'],
    'dólares': ['dolar', 'dolares', 'dollar', '$', 'USD'],
}

# Mapeo de regiones y ejemplos
REGION_EXAMPLES = {
    # Guatemala
    "Petén": {
        "nombres": ["Don Pedro", "Don Manuel", "Don Francisco"],
        "cultivos": ["maíz", "frijol", "pepitoria"],
        "montos": ["25,000", "30,000", "20,000"]
    },
    "Alta Verapaz": {
        "nombres": ["Don Carlos", "Don Miguel", "Don José"],
        "cultivos": ["cardamomo", "café", "cacao"],
        "montos": ["35,000", "40,000", "30,000"]
    },
    "Costa Sur": {
        "nombres": ["Don Roberto", "Don Juan", "Don Antonio"],
        "cultivos": ["caña", "plátano", "palma"],
        "montos": ["45,000", "50,000", "40,000"]
    }
}

class TextProcessor:
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza el texto para procesamiento"""
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover acentos
        text = unidecode(text)
        
        # Remover caracteres especiales
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        # Remover espacios múltiples
        text = ' '.join(text.split())
        
        return text

    @staticmethod
    def fuzzy_match(text: str, options: List[str], threshold: float = 0.85) -> Optional[str]:
        """Encuentra la mejor coincidencia usando fuzzy matching"""
        normalized_text = TextProcessor.normalize_text(text)
        best_match = None
        best_ratio = 0
        
        for option in options:
            normalized_option = TextProcessor.normalize_text(option)
            ratio = fuzz.ratio(normalized_text, normalized_option)
            
            if ratio > threshold and ratio > best_ratio:
                best_match = option
                best_ratio = ratio
        
        return best_match

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extrae números del texto"""
        # Buscar números con diferentes formatos (12.5, 12,5, etc.)
        numbers = re.findall(r'\d+(?:[.,]\d+)?', text)
        return [float(num.replace(',', '.')) for num in numbers]

    @staticmethod
    def get_regional_example(region: str) -> dict[str, str]:
        """Obtiene ejemplo regional para el mensaje de bienvenida"""
        if region not in REGION_EXAMPLES:
            region = list(REGION_EXAMPLES.keys())[0]
        
        example = REGION_EXAMPLES[region]
        return {
            'nombre': example['nombres'][0],
            'cultivo': example['cultivos'][0],
            'monto': example['montos'][0]
        }

class MessageAnalytics:
    def __init__(self, original_text: str, normalized_text: str):
        self.original = original_text
        self.normalized = normalized_text
        self.metrics = {
            'spelling_errors': 0,
            'message_length': len(original_text),
            'words_per_message': len(original_text.split()),
            'unique_words': len(set(original_text.split())),
            'emoji_count': len(re.findall(r'[\U0001F300-\U0001F999]', original_text)),
            'correction_distance': Levenshtein.distance(original_text, normalized_text)
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            'timestamp': datetime.now(),
            'original_text': self.original,
            'normalized_text': self.normalized,
            'metrics': self.metrics
        }
