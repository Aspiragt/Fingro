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
        Genera un reporte financiero simple
        
        Args:
            user_data: Datos del usuario y proyecto
            score_data: Datos del análisis financiero
            
        Returns:
            str: Reporte formateado
        """
        try:
            # Formatear datos básicos
            cultivo = user_data['get_crop'].capitalize()
            area = float(user_data['get_area'])
            # Convertir hectáreas a cuerdas (1 hectárea ≈ 16 cuerdas)
            cuerdas = round(area * 16)
            
            # Obtener precio por unidad
            precio_unidad = score_data.get('price_per_unit', 0)
            if precio_unidad == 0 and score_data.get('expected_yield', 0) > 0:
                # Si no hay precio, calcularlo de los ingresos y rendimiento
                precio_unidad = score_data['expected_income'] / score_data['expected_yield']
            
            # Formatear datos financieros
            costos = cls.format_currency(score_data['total_costs'])
            ingresos = cls.format_currency(score_data['expected_income'])
            ganancia = cls.format_currency(score_data['expected_profit'])
            
            # Calcular rendimiento por cuerda
            rendimiento_total = score_data.get('expected_yield', 0)
            rendimiento_cuerda = round(rendimiento_total / cuerdas) if cuerdas > 0 else 0
            
            # Construir reporte
            report = [
                f"✨ *Análisis de su siembra de {cultivo}*\n",
                f"🌱 *Área:* {cuerdas} cuerdas",
                f"📊 *Rendimiento esperado:* {rendimiento_cuerda} quintales por cuerda",
                f"💰 *Precio de venta:* {cls.format_currency(precio_unidad)} por quintal\n",
                f"💵 *Lo que puede ganar:*",
                f"•⁠  ⁠Ingresos totales: {ingresos}",
                f"•⁠  ⁠Costos de siembra: {costos}",
                f"•⁠  ⁠Ganancia esperada: {ganancia}\n"
            ]
            
            # Si el proyecto es rentable
            if score_data['expected_profit'] > 0:
                # Calcular retorno por cuerda
                ganancia_cuerda = round(score_data['expected_profit'] / cuerdas) if cuerdas > 0 else 0
                report.extend([
                    "✅ *¡Su proyecto puede ser rentable!*",
                    f"Por cada cuerda podría ganar {cls.format_currency(ganancia_cuerda)}"
                ])
            else:
                report.extend([
                    "⚠️ *Recomendaciones para mejorar:*",
                    "• Considere vender a mejor precio (cooperativa o exportación)",
                    "• Mejore el sistema de riego para aumentar rendimiento",
                    "• Reduzca costos comprando insumos al por mayor"
                ])
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}")
            return (
                "❌ Error generando reporte\n\n"
                "Por favor intente de nuevo más tarde."
            )
    
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
