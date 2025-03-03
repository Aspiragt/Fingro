"""
Módulo para evaluación de riesgo crediticio y cálculo del Fingro Score
"""
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class FingroScoreCalculator:
    """
    Calcula el Fingro Score para determinar la capacidad de pago
    y riesgo crediticio de productores agrícolas.
    
    El score va de 0 a 1000 puntos, distribuidos en:
    - Tipo de cultivo: 0-200 puntos
    - Extensión de tierras: 0-200 puntos
    - Método de comercialización: 0-200 puntos
    - Sistema de riego: 0-250 puntos
    - Ubicación del cultivo: 0-150 puntos
    """
    
    def __init__(self):
        # Puntuaciones para cultivos basadas en rentabilidad y demanda
        self.crop_scores = {
            # Cultivos de alto valor y alta demanda
            'aguacate': 200,
            'cafe': 180,
            'cardamomo': 190,
            'mango': 170,
            'macadamia': 180,
            
            # Cultivos de valor medio
            'tomate': 160,
            'chile': 150,
            'papa': 140,
            'cebolla': 140,
            'zanahoria': 130,
            'brocoli': 140,
            'coliflor': 130,
            
            # Granos básicos y cultivos extensivos
            'maiz': 120,
            'frijol': 110,
            'arroz': 130,
            'trigo': 120,
            
            # Otros cultivos
            'platano': 150,
            'limon': 140,
            'naranja': 130,
            'piña': 160,
            'caña': 110
        }
        
        # Puntuaciones para áreas de cultivo
        # Se evalúa en función específica al calcular
        
        # Puntuaciones para métodos de comercialización
        self.channel_scores = {
            'exportacion': 200,      # Más estable y mejores precios
            'cooperativa': 180,      # Apoyo colectivo, precios estables
            'mayorista': 150,        # Buenos volúmenes pero precios variables
            'mercado_local': 120     # Más fluctuación de precios, menores volúmenes
        }
        
        # Puntuaciones para sistemas de riego
        self.irrigation_scores = {
            'goteo': 250,            # Máxima eficiencia y control
            'aspersion': 200,        # Buena eficiencia
            'gravedad': 150,         # Eficiencia media
            'temporal': 80           # Alta dependencia del clima
        }
        
        # Puntuaciones para ubicaciones (departamentos de Guatemala)
        self.location_scores = {
            # Zonas de alta productividad agrícola
            'escuintla': 150,
            'retalhuleu': 140,
            'suchitepequez': 140,
            'santa_rosa': 130,
            'quetzaltenango': 135,
            
            # Zonas de producción de café y cardamomo
            'alta_verapaz': 145,
            'huehuetenango': 140,
            'san_marcos': 130,
            
            # Zona central
            'guatemala': 125,
            'sacatepequez': 130,
            'chimaltenango': 135,
            
            # Zonas del corredor seco
            'el_progreso': 90,
            'zacapa': 95,
            'chiquimula': 100,
            'jalapa': 110,
            'jutiapa': 115,
            
            # Otros departamentos
            'izabal': 120,
            'peten': 115,
            'quiche': 110,
            'baja_verapaz': 105,
            'solola': 125,
            'totonicapan': 115
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza el texto para comparaciones"""
        if not text:
            return ""
        
        import unidecode
        return unidecode.unidecode(text.lower().strip())
    
    def _normalize_location(self, location: str) -> str:
        """Normaliza el nombre del departamento"""
        location = self._normalize_text(location)
        
        # Mapa de variaciones comunes
        location_map = {
            'guatemala': ['ciudad de guatemala', 'ciudad guatemala', 'guatemala city'],
            'quetzaltenango': ['xela', 'xelaju'],
            'alta_verapaz': ['alta verapaz', 'coban'],
            'baja_verapaz': ['baja verapaz', 'salama'],
            'huehuetenango': ['huehue'],
            'quiche': ['el quiche', 'santa cruz del quiche'],
            'san_marcos': ['san marcos'],
            'retalhuleu': ['reu'],
            'sacatepequez': ['la antigua', 'antigua guatemala'],
            'chimaltenango': ['chimal'],
            'escuintla': [],
            'santa_rosa': ['santa rosa', 'cuilapa'],
            'solola': [],
            'totonicapan': ['toto'],
            'suchitepequez': ['suchi', 'mazatenango'],
            'jalapa': [],
            'jutiapa': [],
            'izabal': ['puerto barrios'],
            'zacapa': [],
            'chiquimula': [],
            'el_progreso': ['el progreso', 'guastatoya'],
            'peten': ['flores']
        }
        
        # Buscar coincidencia directa
        for norm_loc, variations in location_map.items():
            if location == norm_loc.replace('_', ' ') or location in variations:
                return norm_loc
        
        # Buscar coincidencia parcial
        for norm_loc, variations in location_map.items():
            if location.startswith(norm_loc.replace('_', ' ')):
                return norm_loc
        
        # Retornar una ubicación por defecto si no hay coincidencias
        return 'guatemala'
    
    def calculate_area_score(self, area: float) -> int:
        """
        Calcula el puntaje basado en el área de cultivo
        
        Args:
            area: Área en hectáreas
            
        Returns:
            Puntaje entre 0-200
        """
        # Modelo de puntaje para área:
        # - Menos de 1 ha: 80-100 (agricultura familiar, mayor riesgo)
        # - 1-5 ha: 100-140 (pequeño productor)
        # - 5-15 ha: 140-180 (mediano productor)
        # - 15-50 ha: 180-200 (productor comercial)
        # - Más de 50 ha: 160-190 (gran productor pero con mayor exposición)
        
        if area < 1:
            return max(80, min(100, int(area * 100)))
        elif area <= 5:
            return 100 + int((area - 1) * 10)
        elif area <= 15:
            return 140 + int((area - 5) * 4)
        elif area <= 50:
            return 180 + int((area - 15) * 0.6)
        else:
            # Para áreas muy grandes, el puntaje puede disminuir por mayor exposición
            return max(160, min(190, 200 - int((area - 50) * 0.2)))
    
    def calculate_fingro_score(self, user_data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """
        Calcula el Fingro Score basado en los datos del usuario
        
        Args:
            user_data: Datos del usuario con información de cultivo, área, etc.
            
        Returns:
            Tuple con (puntaje_total, detalle_por_categoría)
        """
        try:
            score_details = {
                'cultivo': 0,
                'area': 0,
                'comercializacion': 0,
                'riego': 0,
                'ubicacion': 0,
                'total': 0
            }
            
            # 1. Puntaje por tipo de cultivo
            crop = self._normalize_text(user_data.get('crop', ''))
            score_details['cultivo'] = self.crop_scores.get(crop, 100)  # Valor por defecto
            
            # 2. Puntaje por área
            area = float(user_data.get('area', 0))
            score_details['area'] = self.calculate_area_score(area)
            
            # 3. Puntaje por método de comercialización
            channel = user_data.get('channel', '').lower()
            score_details['comercializacion'] = self.channel_scores.get(channel, 120)
            
            # 4. Puntaje por sistema de riego
            irrigation = user_data.get('irrigation', '').lower()
            score_details['riego'] = self.irrigation_scores.get(irrigation, 80)
            
            # 5. Puntaje por ubicación
            location = self._normalize_location(user_data.get('location', ''))
            score_details['ubicacion'] = self.location_scores.get(location, 100)
            
            # Calcular puntaje total
            total_score = sum([
                score_details['cultivo'],
                score_details['area'],
                score_details['comercializacion'],
                score_details['riego'],
                score_details['ubicacion']
            ])
            
            score_details['total'] = total_score
            
            return total_score, score_details
            
        except Exception as e:
            logger.error(f"Error calculando Fingro Score: {str(e)}")
            # Retornar valores por defecto en caso de error
            return 500, {
                'cultivo': 100,
                'area': 100,
                'comercializacion': 100,
                'riego': 100,
                'ubicacion': 100,
                'total': 500
            }
    
    def get_loan_approval_status(self, score: int) -> Tuple[str, str]:
        """
        Determina el estado de aprobación del préstamo basado en el Fingro Score
        
        Args:
            score: Fingro Score calculado
            
        Returns:
            Tuple con (estado_aprobacion, mensaje_explicativo)
        """
        if score >= 800:
            return "APROBADO", (
                "¡Felicidades! 🎉 Su préstamo ha sido aprobado automáticamente. "
                "Su perfil agrícola muestra un excelente potencial de éxito."
            )
        elif score >= 500:
            return "EVALUACIÓN", (
                "Su préstamo requiere una evaluación manual adicional. 🔍 "
                "Su perfil muestra buen potencial, pero necesitamos revisar "
                "algunos detalles para asegurar el éxito de su proyecto."
            )
        else:
            return "RECHAZADO", (
                "Lo sentimos, su préstamo no puede ser aprobado en este momento. 🌱 "
                "Le recomendamos mejorar aspectos clave como su sistema de riego o "
                "diversificar sus canales de comercialización para aumentar sus "
                "posibilidades de aprobación en el futuro."
            )

# Instancia global del calculador
score_calculator = FingroScoreCalculator()
