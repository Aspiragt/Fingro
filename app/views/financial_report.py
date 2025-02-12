"""
Módulo para generar reportes financieros
"""
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FinancialReport:
    """Genera reportes financieros formatados para WhatsApp"""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Formatea cantidades monetarias"""
        return f"Q{amount:,.2f}"
    
    @classmethod
    def generate_report(cls, user_data: Dict[str, Any], score_data: Dict[str, Any]) -> str:
        """
        Genera un reporte financiero en formato amigable
        
        Args:
            user_data: Datos del usuario
            score_data: Datos del análisis financiero
            
        Returns:
            str: Reporte formateado
        """
        try:
            # Redondear números
            area = round(score_data['area'])
            rendimiento = round(score_data['rendimiento_por_hectarea'])
            precio = round(score_data['precio_actual'], 2)
            ingresos = round(score_data['ingresos_totales'])
            costos = round(score_data['costos_totales'])
            ganancia = round(score_data['ganancia_total'])
            ganancia_hectarea = round(score_data['ganancia_por_hectarea'])
            
            # Generar reporte
            report = [
                f"✨ Análisis de su siembra de {score_data['cultivo'].capitalize()}\n",
                f"🌱 Área: {area} hectáreas",
                f"📊 Rendimiento esperado: {rendimiento} quintales por hectárea",
                f"💰 Precio de venta: Q{precio:,.2f} por {score_data['medida']}",
                "",
                "💵 Lo que puede ganar:",
                f"•⁠  ⁠Ingresos totales: Q{ingresos:,.2f}",
                f"•⁠  ⁠Costos de siembra: Q{costos:,.2f}",
                f"•⁠  ⁠Ganancia esperada: Q{ganancia:,.2f}",
                "",
                "✅ ¡Su proyecto puede ser rentable!",
                f"Por cada hectárea podría ganar Q{ganancia_hectarea:,.2f}"
            ]
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}")
            return "❌ Error generando reporte"
    
    @classmethod
    def generate_loan_offer(cls, score_data: Dict[str, Any]) -> str:
        """
        Genera oferta de préstamo
        
        Args:
            score_data: Datos del análisis financiero
            
        Returns:
            str: Oferta formateada
        """
        try:
            prestamo = cls.format_currency(score_data['recommended_loan'])
            cuota = cls.format_currency(score_data['monthly_payment'])
            
            offer = [
                "💳 *Préstamo pre-aprobado*\n",
                f"• Monto: {prestamo}",
                f"• Cuota mensual: {cuota}",
                "• Plazo: 12 meses",
                "• Tasa: 15% anual\n",
                "¿Deseas enviar tu solicitud ahora?",
                "Responde *SI* o *NO*"
            ]
            
            return "\n".join(offer)
            
        except Exception as e:
            return (
                "❌ Error generando oferta\n\n"
                "Por favor intenta de nuevo más tarde."
            )
    
    @staticmethod
    def generate_success_message() -> str:
        """Genera mensaje de solicitud enviada"""
        return (
            "✅ *¡Solicitud enviada con éxito!*\n\n"
            "Pronto nos pondremos en contacto contigo.\n"
            "Escribe *otra* para analizar otro cultivo."
        )

# Instancia global
report_generator = FinancialReport()
