"""
API para obtener precios de productos agrícolas del MAGA usando datos predefinidos
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MagaAPI:
    """Cliente para el API de precios del MAGA"""
    
    def __init__(self):
        """Inicializa el cliente de MAGA"""
        # Diccionario de cultivos y sus variaciones
        self.crops = {
            # Granos básicos
            'maiz': {
                'nombre': 'Maíz blanco, de primera',
                'precio': 173.13,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'frijol_negro': {
                'nombre': 'Frijol negro, de primera',
                'precio': 688.75,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'frijol_rojo': {
                'nombre': 'Frijol rojo, de primera',
                'precio': 800.00,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'frijol_blanco': {
                'nombre': 'Frijol blanco, de primera',
                'precio': 968.75,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'arroz': {
                'nombre': 'Arroz oro, blanco de primera',
                'precio': 440.00,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'sorgo': {
                'nombre': 'Sorgo blanco, de primera',
                'precio': 175.00,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },

            # Hortalizas
            'papa': {
                'nombre': 'Papa Loman, lavada, grande, de primera',
                'precio': 314.69,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'tomate': {
                'nombre': 'Tomate de cocina, grande, de primera',
                'precio': 152.81,
                'unidad': 'Caja (45 - 50 lb)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'cebolla': {
                'nombre': 'Cebolla seca, blanca, mediana, de primera',
                'precio': 395.00,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'chile_pimiento': {
                'nombre': 'Chile Pimiento, grande, de primera',
                'precio': 131.88,
                'unidad': 'Caja (90 -100 unidades)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'zanahoria': {
                'nombre': 'Zanahoria mediana, de primera',
                'precio': 43.13,
                'unidad': 'Red (7 - 8 docenas)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'remolacha': {
                'nombre': 'Remolacha mediana, de primera',
                'precio': 42.03,
                'unidad': 'Red (4 - 5 docenas)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'guisquil': {
                'nombre': 'Güisquil mediano, de primera',
                'precio': 177.97,
                'unidad': 'Ciento',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'brocoli': {
                'nombre': 'Brócoli mediano, de primera',
                'precio': 135.63,
                'unidad': 'Bolsa (2 docenas)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'coliflor': {
                'nombre': 'Coliflor mediana, de primera',
                'precio': 79.38,
                'unidad': 'Red (13 - 15 unidades)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'repollo': {
                'nombre': 'Repollo blanco, mediano, de primera',
                'precio': 43.13,
                'unidad': 'Red',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'apio': {
                'nombre': 'Apio mediano, de primera',
                'precio': 60.00,
                'unidad': 'Docena',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'pepino': {
                'nombre': 'Pepino mediano, de primera',
                'precio': 129.22,
                'unidad': 'Caja (50 - 60 unidades)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'ejote': {
                'nombre': 'Ejote francés, revuelto, de primera',
                'precio': 175.00,
                'unidad': 'Costal (40 lb)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'arveja': {
                'nombre': 'Arveja china, revuelta, de primera',
                'precio': 440.00,
                'unidad': 'Costal (40 lb)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'yuca': {
                'nombre': 'Yuca entera, mediana, de primera',
                'precio': 201.88,
                'unidad': 'Red (75 - 80 unidades)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },

            # Frutas
            'aguacate': {
                'nombre': 'Aguacate Hass, mediano, importado',
                'precio': 105.00,
                'unidad': 'Caja (7 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'banano': {
                'nombre': 'Banano criollo, mediano, de primera',
                'precio': 171.56,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'mango': {
                'nombre': 'Mango Tommy Atkins, mediano',
                'precio': 250.00,
                'unidad': 'Ciento (50 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'papaya': {
                'nombre': 'Papaya Tainung, mediana, de primera',
                'precio': 108.75,
                'unidad': 'Caja (40 lb)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'piña': {
                'nombre': 'Piña mediana',
                'precio': 631.25,
                'unidad': 'Ciento (105 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'melon': {
                'nombre': 'Melón Cantaloupe, mediano',
                'precio': 800.00,
                'unidad': 'Ciento (75 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'sandia': {
                'nombre': 'Sandia redonda, mediana',
                'precio': 2000.00,
                'unidad': 'Ciento (177.35 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'limon': {
                'nombre': 'Limón Persa, mediano',
                'precio': 425.00,
                'unidad': 'Millar (110 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'naranja': {
                'nombre': 'Naranja Valencia, mediana, de primera de origen hondureño',
                'precio': 102.19,
                'unidad': 'Ciento (23.9 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'mandarina': {
                'nombre': 'Mandarina criolla, mediana, de primera',
                'precio': 125.78,
                'unidad': 'Ciento (13.25 kg)',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'manzana': {
                'nombre': 'Manzana Estrella, mediana',
                'precio': 658.75,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },

            # Especias y otros
            'achiote': {
                'nombre': 'Achiote seco, sin capsula, de primera',
                'precio': 1000.00,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'chile_seco': {
                'nombre': 'Chile Cobanero, seco, de primera',
                'precio': 7500.00,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'rosa_jamaica': {
                'nombre': 'Rosa Jamaica, nacional',
                'precio': 4300.00,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            },
            'loroco': {
                'nombre': 'Loroco de primera',
                'precio': 3793.75,
                'unidad': 'Quintal',
                'fecha': '2025-02-12',
                'mercado': 'La Terminal',
                'fuente': 'MAGA'
            }
        }
        
        # Mapeo de variaciones de nombres
        self.name_mapping = {
            # Granos básicos
            'maiz': 'maiz',
            'maíz': 'maiz',
            'mais': 'maiz',
            'maís': 'maiz',
            'elote': 'maiz',
            
            'frijol negro': 'frijol_negro',
            'frijol': 'frijol_negro',
            'frijoles negros': 'frijol_negro',
            
            'frijol rojo': 'frijol_rojo',
            'frijoles rojos': 'frijol_rojo',
            
            'frijol blanco': 'frijol_blanco',
            'frijoles blancos': 'frijol_blanco',
            
            'arroz': 'arroz',
            'arroz blanco': 'arroz',
            'arroz de primera': 'arroz',
            
            'sorgo': 'sorgo',
            'sorgo blanco': 'sorgo',
            'maicillo': 'sorgo',
            
            # Hortalizas
            'papa': 'papa',
            'papas': 'papa',
            'papa loman': 'papa',
            'papa grande': 'papa',
            
            'tomate': 'tomate',
            'tomates': 'tomate',
            'jitomate': 'tomate',
            'tomate de cocina': 'tomate',
            
            'cebolla': 'cebolla',
            'cebollas': 'cebolla',
            'cebolla blanca': 'cebolla',
            'cebolla seca': 'cebolla',
            
            'chile': 'chile_pimiento',
            'chile pimiento': 'chile_pimiento',
            'pimiento': 'chile_pimiento',
            'chiles': 'chile_pimiento',
            'morron': 'chile_pimiento',
            'morrón': 'chile_pimiento',
            
            'brocoli': 'brocoli',
            'brócoli': 'brocoli',
            'brecol': 'brocoli',
            
            'zanahoria': 'zanahoria',
            'zanahorias': 'zanahoria',
            
            'repollo': 'repollo',
            'col': 'repollo',
            
            'apio': 'apio',
            'apios': 'apio',
            
            'pepino': 'pepino',
            'pepinos': 'pepino',
            
            'ejote': 'ejote',
            'ejotes': 'ejote',
            'ejote frances': 'ejote',
            
            'arveja': 'arveja',
            'arvejas': 'arveja',
            'arveja china': 'arveja',
            
            'yuca': 'yuca',
            'yucas': 'yuca',
            
            # Frutas
            'aguacate': 'aguacate',
            'aguacates': 'aguacate',
            'aguacate hass': 'aguacate',
            'palta': 'aguacate',
            
            'banano': 'banano',
            'bananos': 'banano',
            'platano': 'banano',
            'plátano': 'banano',
            
            'mango': 'mango',
            'mangos': 'mango',
            'mango tommy': 'mango',
            
            'papaya': 'papaya',
            'papayas': 'papaya',
            
            'piña': 'piña',
            'piñas': 'piña',
            
            'melon': 'melon',
            'melón': 'melon',
            'melones': 'melon',
            
            'sandia': 'sandia',
            'sandía': 'sandia',
            'sandias': 'sandia',
            'sandías': 'sandia',
            
            'limon': 'limon',
            'limón': 'limon',
            'limones': 'limon',
            
            'naranja': 'naranja',
            'naranjas': 'naranja',
            
            'mandarina': 'mandarina',
            'mandarinas': 'mandarina',
            
            'manzana': 'manzana',
            'manzanas': 'manzana',
            
            # Especias y otros
            'achiote': 'achiote',
            
            'chile seco': 'chile_seco',
            'chile cobanero': 'chile_seco',
            'chile chocolate': 'chile_seco',
            
            'rosa jamaica': 'rosa_jamaica',
            'flor de jamaica': 'rosa_jamaica',
            'jamaica': 'rosa_jamaica',
            
            'loroco': 'loroco'
        }
        
        self.variations = {
            'maiz': 'maiz',
            'maíz': 'maiz',
            'mais': 'maiz',
            'maís': 'maiz',
            'elote': 'maiz',
            
            'frijol negro': 'frijol_negro',
            'frijol': 'frijol_negro',
            'frijoles negros': 'frijol_negro',
            
            'frijol rojo': 'frijol_rojo',
            'frijoles rojos': 'frijol_rojo',
            
            'frijol blanco': 'frijol_blanco',
            'frijoles blancos': 'frijol_blanco',
            
            'arroz': 'arroz',
            'arroz blanco': 'arroz',
            'arroz de primera': 'arroz',
            
            'sorgo': 'sorgo',
            'sorgo blanco': 'sorgo',
            'maicillo': 'sorgo',
            
            # Hortalizas
            'papa': 'papa',
            'papas': 'papa',
            'papa loman': 'papa',
            'papa grande': 'papa',
            
            'tomate': 'tomate',
            'tomates': 'tomate',
            'jitomate': 'tomate',
            'tomate de cocina': 'tomate',
            
            'cebolla': 'cebolla',
            'cebollas': 'cebolla',
            'cebolla blanca': 'cebolla',
            'cebolla seca': 'cebolla',
            
            'chile': 'chile_pimiento',
            'chile pimiento': 'chile_pimiento',
            'pimiento': 'chile_pimiento',
            'chiles': 'chile_pimiento',
            'morron': 'chile_pimiento',
            'morrón': 'chile_pimiento',
            
            'brocoli': 'brocoli',
            'brócoli': 'brocoli',
            'brecol': 'brocoli',
            
            'zanahoria': 'zanahoria',
            'zanahorias': 'zanahoria',
            
            'repollo': 'repollo',
            'col': 'repollo',
            
            'apio': 'apio',
            'apios': 'apio',
            
            'pepino': 'pepino',
            'pepinos': 'pepino',
            
            'ejote': 'ejote',
            'ejotes': 'ejote',
            'ejote frances': 'ejote',
            
            'arveja': 'arveja',
            'arvejas': 'arveja',
            'arveja china': 'arveja',
            
            'yuca': 'yuca',
            'yucas': 'yuca',
            
            # Frutas
            'aguacate': 'aguacate',
            'aguacates': 'aguacate',
            'aguacate hass': 'aguacate',
            'palta': 'aguacate',
            
            'banano': 'banano',
            'bananos': 'banano',
            'platano': 'banano',
            'plátano': 'banano',
            
            'mango': 'mango',
            'mangos': 'mango',
            'mango tommy': 'mango',
            
            'papaya': 'papaya',
            'papayas': 'papaya',
            
            'piña': 'piña',
            'piñas': 'piña',
            
            'melon': 'melon',
            'melón': 'melon',
            'melones': 'melon',
            
            'sandia': 'sandia',
            'sandía': 'sandia',
            'sandias': 'sandia',
            'sandías': 'sandia',
            
            'limon': 'limon',
            'limón': 'limon',
            'limones': 'limon',
            
            'naranja': 'naranja',
            'naranjas': 'naranja',
            
            'mandarina': 'mandarina',
            'mandarinas': 'mandarina',
            
            'manzana': 'manzana',
            'manzanas': 'manzana',
            
            # Especias y otros
            'achiote': 'achiote',
            
            'chile seco': 'chile_seco',
            'chile cobanero': 'chile_seco',
            'chile chocolate': 'chile_seco',
            
            'rosa jamaica': 'rosa_jamaica',
            'flor de jamaica': 'rosa_jamaica',
            'jamaica': 'rosa_jamaica',
            
            'loroco': 'loroco',
            
            # Errores comunes adicionales
            'sandilla': 'sandia',
            'zanaoria': 'zanahoria',
            'zanoria': 'zanahoria',
            'broculi': 'brocoli',
            'brocolin': 'brocoli',
            'chile morron': 'chile_pimiento',
            'pimiento morron': 'chile_pimiento',
            'tomate de cosina': 'tomate',
            'aguacate jass': 'aguacate',
            'guineo': 'banano',
            'platanos': 'banano',
            'elotes': 'maiz',
            'maiz elote': 'maiz',
            'frijoles': 'frijol_negro',
            'limon persa': 'limon',
            'limon criollo': 'limon',
            'naranja agria': 'naranja',
            'naranja dulce': 'naranja',
            'papas': 'papa',
            'patatas': 'papa'
        }
        
        logger.info("MagaAPI inicializado con datos predefinidos")
    
    def _normalize_text(self, text):
        """Normaliza el texto para búsqueda
        
        Args:
            text (str): Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        if not text:
            return ""
            
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover acentos
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n'
        }
        for a, b in replacements.items():
            text = text.replace(a, b)
            
        # Corregir errores comunes
        common_mistakes = {
            'sandilla': 'sandia',
            'zanaoria': 'zanahoria',
            'zanoria': 'zanahoria',
            'broculi': 'brocoli',
            'brocolin': 'brocoli',
            'chile morron': 'chile pimiento',
            'chile morró': 'chile pimiento',
            'chile morrón': 'chile pimiento',
            'tomate de cosina': 'tomate de cocina',
            'aguacate jass': 'aguacate hass',
            'pimiento morron': 'chile pimiento',
            'frijoles': 'frijol',
            'elotes': 'maiz',
            'platanos': 'platano',
            'guineo': 'banano',
            'limon persa': 'limon',
            'naranja agria': 'naranja',
            'papas': 'papa'
        }
        
        # Aplicar correcciones de errores comunes
        for mistake, correction in common_mistakes.items():
            if mistake in text:
                text = text.replace(mistake, correction)
            
        # Remover caracteres especiales
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        
        # Remover espacios extra
        text = ' '.join(text.split())
        
        return text

    def get_crop_info(self, crop_name):
        """Obtiene la información de un cultivo
        
        Args:
            crop_name (str): Nombre del cultivo a buscar
            
        Returns:
            dict: Información del cultivo o None si no se encuentra
        """
        if not crop_name:
            return None
            
        # Normalizar el nombre del cultivo
        normalized_name = self._normalize_text(crop_name)
        
        # Buscar coincidencias exactas primero
        if normalized_name in self.variations:
            crop_key = self.variations[normalized_name]
            return self.crops[crop_key]
            
        # Si no hay coincidencia exacta, buscar coincidencias parciales
        for variation, key in self.variations.items():
            # Normalizar la variación
            normalized_variation = self._normalize_text(variation)
            
            # Verificar si el nombre del cultivo está contenido en la variación
            # o si la variación está contenida en el nombre del cultivo
            if (normalized_name in normalized_variation or 
                normalized_variation in normalized_name):
                return self.crops[key]
                
        # Si aún no hay coincidencia, buscar palabras individuales
        crop_words = set(normalized_name.split())
        
        best_match = None
        max_word_matches = 0
        
        for variation, key in self.variations.items():
            variation_words = set(self._normalize_text(variation).split())
            word_matches = len(crop_words.intersection(variation_words))
            
            if word_matches > max_word_matches:
                max_word_matches = word_matches
                best_match = key
        
        if best_match and max_word_matches > 0:
            return self.crops[best_match]
            
        return None

    async def search_crop(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Busca un cultivo en los datos predefinidos
        
        Args:
            query: Nombre del cultivo a buscar
            
        Returns:
            Dict con información del cultivo o None si no se encuentra
        """
        try:
            # Normalizar búsqueda
            query = query.lower().strip()
            logger.info(f"Buscando cultivo: {query}")
            
            # Buscar en el mapeo de nombres
            crop_key = self.name_mapping.get(query)
            if not crop_key:
                logger.warning(f"Cultivo no encontrado en mapeo: {query}")
                return None
            
            # Obtener datos del cultivo
            crop_data = self.crops.get(crop_key)
            if not crop_data:
                logger.warning(f"Cultivo no encontrado en datos: {crop_key}")
                return None
            
            logger.info(f"Cultivo encontrado: {crop_data}")
            return crop_data
            
        except Exception as e:
            logger.error(f"Error buscando cultivo: {str(e)}")
            return None
    
    async def get_historical_prices(self, query: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtiene historial de precios para un cultivo
        
        Args:
            query: Nombre del cultivo
            days: Número de días de historial
            
        Returns:
            Lista de precios históricos
        """
        try:
            crop_data = await self.search_crop(query)
            if not crop_data:
                return []
            
            # Por ahora solo retornamos el precio actual
            return [crop_data]
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {str(e)}")
            return []

# Instancia global del API
maga_api = MagaAPI()
