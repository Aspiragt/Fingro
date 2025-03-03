"""
Módulo para presentar resultados financieros a los agricultores
con lenguaje simple y acorde a su contexto cultural.
"""
from typing import Dict, Any, Tuple, List
import logging
from app.utils.currency import format_currency
from app.scoring.credit_score import score_calculator

logger = logging.getLogger(__name__)

class FinancialResultsPresenter:
    """
    Presenta los resultados financieros y de puntuación
    de manera amigable para agricultores guatemaltecos.
    """
    
    def __init__(self):
        # Recomendaciones específicas por categoría
        self.recommendations = {
            'cultivo': {
                'bajo': (
                    "Los cultivos como el aguacate 🥑, café ☕ o cardamomo rinden "
                    "mejores ganancias que los cultivos tradicionales."
                ),
                'medio': (
                    "Su cultivo actual tiene buen potencial. Podría considerar "
                    "diversificar con otros cultivos complementarios 🌱."
                ),
                'alto': (
                    "¡Excelente elección de cultivo! Tiene muy buen valor en el mercado 👍."
                )
            },
            'area': {
                'bajo': (
                    "Aumentar el área de siembra le permitiría mejorar sus ingresos. "
                    "¿Ha considerado alquilar más terreno? 🌾"
                ),
                'medio': (
                    "El tamaño de su terreno es adecuado. Enfóquese en mejorar el rendimiento "
                    "por cuerda para maximizar ganancias 📈."
                ),
                'alto': (
                    "¡Tiene una extensión de tierra muy favorable! Esto le permite "
                    "planificar bien sus siembras."
                )
            },
            'comercializacion': {
                'bajo': (
                    "Vender directamente a mercados locales limita sus ganancias. "
                    "¿Ha considerado unirse a una cooperativa? 🤝"
                ),
                'medio': (
                    "Trabajar con mayoristas es bueno. La próxima vez, intente negociar "
                    "mejores precios mostrando la calidad de su producto 🚚."
                ),
                'alto': (
                    "¡Excelente canal de venta! La exportación y venta organizada "
                    "le aseguran los mejores precios del mercado 💰."
                )
            },
            'riego': {
                'bajo': (
                    "Depender solo de la lluvia es riesgoso. Un sistema de riego simple "
                    "podría ayudarle a sembrar todo el año 💧."
                ),
                'medio': (
                    "Su sistema de riego actual es bueno. Mantenerlo en buen estado "
                    "es importante para asegurar su cosecha 🌊."
                ),
                'alto': (
                    "¡Su sistema de riego es excelente! Esto asegura buenas cosechas "
                    "incluso en época seca 👏."
                )
            },
            'ubicacion': {
                'bajo': (
                    "Su zona tiene algunos desafíos para la agricultura. Consulte con el "
                    "técnico agrícola sobre cultivos más resistentes 🧑‍🌾."
                ),
                'medio': (
                    "Su ubicación tiene buen potencial agrícola. Aproveche los programas "
                    "de asistencia técnica disponibles en su región 🗺️."
                ),
                'alto': (
                    "¡Está en una de las mejores zonas agrícolas! Su ubicación favorece "
                    "cultivos de alta calidad ✨."
                )
            }
        }
        
    def get_category_level(self, category: str, score: int) -> str:
        """
        Determina el nivel de una categoría basado en su puntaje
        
        Args:
            category: Nombre de la categoría
            score: Puntaje obtenido
            
        Returns:
            Nivel (bajo, medio, alto)
        """
        # Determinar umbrales según la categoría
        if category == 'cultivo':
            if score < 120:
                return 'bajo'
            elif score < 160:
                return 'medio'
            else:
                return 'alto'
        elif category == 'area':
            if score < 120:
                return 'bajo'
            elif score < 160:
                return 'medio'
            else:
                return 'alto'
        elif category == 'comercializacion':
            if score < 130:
                return 'bajo'
            elif score < 180:
                return 'medio'
            else:
                return 'alto'
        elif category == 'riego':
            if score < 120:
                return 'bajo'
            elif score < 200:
                return 'medio'
            else:
                return 'alto'
        elif category == 'ubicacion':
            if score < 100:
                return 'bajo'
            elif score < 130:
                return 'medio'
            else:
                return 'alto'
        else:
            return 'medio'  # Valor por defecto
    
    def get_recommendations(self, score_details: Dict[str, int]) -> List[str]:
        """
        Genera recomendaciones personalizadas basadas en los puntajes
        
        Args:
            score_details: Detalle de puntajes por categoría
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Encontrar las dos categorías con puntuación más baja
        categories = ['cultivo', 'area', 'comercializacion', 'riego', 'ubicacion']
        category_scores = [(cat, score_details.get(cat, 0)) for cat in categories]
        category_scores.sort(key=lambda x: x[1])  # Ordenar por puntaje ascendente
        
        # Generar recomendaciones para las dos categorías más bajas
        for category, score in category_scores[:2]:
            level = self.get_category_level(category, score)
            if level == 'bajo' or level == 'medio':
                recommendations.append(self.recommendations[category][level])
        
        # Si no hay recomendaciones de bajo nivel, incluir una general
        if not recommendations:
            recommendations.append(
                "Su perfil agrícola es muy sólido. Para mejorar aún más, "
                "considere nuevas tecnologías o métodos de cultivo 🌟."
            )
        
        return recommendations
    
    def format_financial_analysis(self, user_data: Dict[str, Any]) -> str:
        """
        Genera un análisis financiero formateado para WhatsApp
        
        Args:
            user_data: Datos del usuario con información completa
            
        Returns:
            Mensaje formateado para WhatsApp
        """
        try:
            from app.utils.loan_calculator import calculate_loan_amount
            
            # Calcular Fingro Score
            score, score_details = score_calculator.calculate_fingro_score(user_data)
            status, message = score_calculator.get_loan_approval_status(score)
            
            # Obtener recomendaciones personalizadas
            recommendations = self.get_recommendations(score_details)
            
            # Obtener área y calcular monto de préstamo según tarifas predeterminadas
            area = float(user_data.get('area', 1))
            max_loan = calculate_loan_amount(area)
            
            # Redondear a miles más cercanos para simplicidad
            max_loan = round(max_loan / 1000) * 1000
            
            # Formatear mensaje según el estado de aprobación
            crop_name = user_data.get('crop', 'cultivo').capitalize()
            
            # Mensaje base dependiendo del status de aprobación
            if status == "APROBADO":  # Aprobación inmediata
                analysis = f"""
📊 *Análisis de su proyecto de {crop_name}*

*¡Felicitaciones! Su Fingro Score es: {score} puntos* ✨
{message}

*Monto máximo aprobado: {format_currency(max_loan)}*
Este monto está calculado para su área de {area} {'hectárea' if area == 1 else 'hectáreas'} de {crop_name}.

¿Desea recibir su préstamo ahora? 💰

Responda *SÍ* para continuar o *NO* para finalizar.
"""
            elif status == "EVALUACIÓN":  # Evaluación manual
                analysis = f"""
📊 *Análisis de su proyecto de {crop_name}*

*Su Fingro Score es: {score} puntos*
{message}

*Monto máximo recomendado: {format_currency(max_loan)}*
Este monto está calculado para su área de {area} {'hectárea' if area == 1 else 'hectáreas'} de {crop_name}.

*Recomendaciones para mejorar:*
"""
                # Agregar recomendaciones
                for i, recommendation in enumerate(recommendations, 1):
                    analysis += f"{i}. {recommendation}\n"
                
                analysis += f"""
¿Le interesa continuar con su solicitud de préstamo de hasta {format_currency(max_loan)}? 📝
El proceso tomará 48 horas para aprobación.

Responda *SÍ* para continuar o *NO* para finalizar.
"""

            else:  # Rechazo con recomendaciones
                analysis = f"""
📊 *Análisis de su proyecto de {crop_name}*

*Su Fingro Score es: {score} puntos*
{message}

*Recomendaciones para mejorar su perfil agrícola:*
"""
                # Agregar recomendaciones
                for i, recommendation in enumerate(recommendations, 1):
                    analysis += f"{i}. {recommendation}\n"
                
                analysis += f"""
Puede volver a solicitar su préstamo cuando haya implementado estas mejoras. También ofrecemos asesoría digital gratuita en www.fingro.gt/recursos para ayudarle a mejorar su proyecto.

¿Desea recibir información adicional sobre cómo mejorar su puntaje? 📚

Responda *SÍ* para recibir recursos o *NO* para finalizar.
"""
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generando análisis financiero: {str(e)}")
            # Mensaje genérico en caso de error
            return (
                "📊 *Análisis de su proyecto agrícola*\n\n"
                "Hemos revisado su información y podemos ofrecerle financiamiento "
                "para su proyecto. ¿Le interesa continuar con la solicitud? 📝\n\n"
                "Responda *SÍ* para recibir su aplicación o *NO* para finalizar."
            )

# Instancia global del presentador
financial_presenter = FinancialResultsPresenter()
