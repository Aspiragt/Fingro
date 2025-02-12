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
            cultivo = user_data['crop'].capitalize()
            area = f"{user_data['area']:,.1f}"
            
            # Formatear datos financieros
            costos = cls.format_currency(score_data['total_costs'])
            ingresos = cls.format_currency(score_data['expected_income'])
            ganancia = cls.format_currency(score_data['expected_profit'])
            
            # Construir reporte
            report = [
                f"✨ *Análisis de {cultivo}* ({area} hectáreas)\n",
                f"💰 *Ingresos esperados:* {ingresos}",
                f"💸 *Costos totales:* {costos}",
                f"✅ *Ganancia potencial:* {ganancia}\n",
            ]
            
            # Si el proyecto es rentable, ofrecer préstamo
            if score_data['expected_profit'] > 0:
                report.extend([
                    "🎯 *¡Tu proyecto es viable!*",
                    "¿Te gustaría solicitar un préstamo para iniciarlo?",
                    "Responde *SI* o *NO*"
                ])
            else:
                report.extend([
                    "❌ Los costos son mayores que los ingresos esperados.",
                    "Te recomendamos revisar otras opciones.",
                    "Escribe *otra* para analizar otro cultivo."
                ])
            
            return "\n".join(report)
            
        except Exception as e:
            return (
                "❌ Error generando reporte\n\n"
                "Por favor intenta de nuevo más tarde."
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
