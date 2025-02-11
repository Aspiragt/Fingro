"""
Módulo para generar reportes financieros
"""
from typing import Dict, Any
from datetime import datetime

class FinancialReport:
    """Genera reportes financieros formatados para WhatsApp"""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Formatea cantidades monetarias"""
        return f"Q{amount:,.2f}"
    
    @staticmethod
    def format_number(number: float) -> str:
        """Formatea números con separadores de miles"""
        return f"{number:,.2f}"
    
    @classmethod
    def generate_detailed_report(cls, user_data: Dict[str, Any], score_data: Dict[str, Any]) -> str:
        """
        Genera un reporte financiero detallado formateado para WhatsApp
        """
        try:
            # Datos básicos
            cultivo = user_data.get('cultivo', 'No especificado')
            hectareas = float(user_data.get('hectareas', 0))
            riego = user_data.get('riego', 'No especificado')
            comercializacion = user_data.get('comercializacion', 'No especificado')
            ubicacion = user_data.get('ubicacion', 'No especificado')
            
            # Datos de precios
            precio_info = user_data.get('precio_info', {})
            precio_actual = float(precio_info.get('precio_actual', 0))
            tendencia = precio_info.get('tendencia', 'estable')
            unidad = precio_info.get('unidad_medida', 'quintal')
            
            # Datos del score
            fingro_score = score_data.get('fingro_score', 0)
            prestamo = score_data.get('prestamo_recomendado', 0)
            produccion = score_data.get('produccion_estimada', 0)
            ingreso = score_data.get('ingreso_estimado', 0)
            scores = score_data.get('scores_detallados', {})
            
            # Construir reporte
            report = [
                "📊 *REPORTE FINANCIERO DETALLADO*\n",
                
                "*📝 Datos del Proyecto*",
                f"• Cultivo: {cultivo}",
                f"• Área: {cls.format_number(hectareas)} hectáreas",
                f"• Sistema de riego: {riego}",
                f"• Comercialización: {comercializacion}",
                f"• Ubicación: {ubicacion}\n",
                
                "*💰 Análisis de Mercado*",
                f"• Precio actual: {cls.format_currency(precio_actual)}/{unidad}",
                f"• Tendencia: {tendencia}",
                f"• Producción estimada: {cls.format_number(produccion)} {unidad}s",
                f"• Ingreso proyectado: {cls.format_currency(ingreso)}\n",
                
                "*📈 Fingro Score*",
                f"• Score general: {fingro_score}%",
                "• Desglose:",
                f"  - Área: {scores.get('area_size', 0)}%",
                f"  - Riego: {scores.get('irrigation', 0)}%",
                f"  - Mercado: {scores.get('market_access', 0)}%",
                f"  - Precios: {scores.get('price_trend', 0)}%",
                f"  - Ubicación: {scores.get('location', 0)}%\n",
                
                "*💳 Préstamo Recomendado*",
                f"• Monto: {cls.format_currency(prestamo)}\n",
                
                "🏦 *¿Listo para solicitar tu préstamo?*",
                "Escribe 'solicitar' para comenzar el proceso."
            ]
            
            return "\n".join(report)
            
        except Exception as e:
            return ("❌ Lo siento, hubo un error generando el reporte. "
                   "Por favor, intenta nuevamente o contacta a soporte.")

# Instancia global
report_generator = FinancialReport()
