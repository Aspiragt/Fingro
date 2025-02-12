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
        
        Args:
            user_data: Datos del usuario y proyecto
            score_data: Datos del análisis financiero
            
        Returns:
            str: Reporte formateado
        """
        try:
            # Formatear datos básicos
            cultivo = user_data['crop'].capitalize()
            area = cls.format_number(user_data['area'])
            riego = user_data['irrigation']
            comercializacion = user_data['commercialization']
            ubicacion = user_data.get('location', 'No especificada')
            
            # Formatear datos financieros
            score = score_data['score']
            riesgo = score_data['risk_level']
            costos = cls.format_currency(score_data['total_costs'])
            produccion = cls.format_number(score_data['expected_yield'])
            ingresos = cls.format_currency(score_data['expected_income'])
            ganancia = cls.format_currency(score_data['expected_profit'])
            roi = cls.format_number(score_data['roi'])
            
            # Formatear datos del préstamo
            prestamo = cls.format_currency(score_data['recommended_loan'])
            cuota = cls.format_currency(score_data['monthly_payment'])
            
            # Formatear precios
            precio_base = cls.format_currency(score_data['price_info']['base_price'])
            precio_ajustado = cls.format_currency(score_data['price_info']['adjusted_price'])
            
            # Construir reporte
            report = [
                "📊 *ANÁLISIS FINANCIERO*\n",
                
                "*📝 Datos del Proyecto*",
                f"• Cultivo: {cultivo}",
                f"• Área: {area} hectáreas",
                f"• Riego: {riego}",
                f"• Comercialización: {comercializacion}",
                f"• Ubicación: {ubicacion}\n",
                
                "*💰 Análisis de Costos y Ganancias*",
                f"• Costos totales: {costos}",
                f"• Producción esperada: {produccion} quintales",
                f"• Precio base: {precio_base}/quintal",
                f"• Precio ajustado: {precio_ajustado}/quintal",
                f"• Ingresos esperados: {ingresos}",
                f"• Ganancia potencial: {ganancia}",
                f"• Retorno sobre inversión: {roi}%\n",
                
                "*📈 Evaluación de Riesgo*",
                f"• FinGro Score: {score}/1000",
                f"• Nivel de riesgo: {riesgo}\n",
                
                "*💳 Préstamo Recomendado*",
                f"• Monto: {prestamo}",
                f"• Cuota mensual: {cuota}/mes",
                "• Plazo: 12 meses",
                "• Tasa: 15% anual"
            ]
            
            return "\n".join(report)
            
        except Exception as e:
            return (
                "❌ Error generando reporte\n\n"
                "Por favor contacta a soporte técnico."
            )
    
    @classmethod
    def generate_simple_report(cls, user_data: Dict[str, Any], score_data: Dict[str, Any]) -> str:
        """
        Genera un reporte financiero simplificado
        
        Args:
            user_data: Datos del usuario y proyecto
            score_data: Datos del análisis financiero
            
        Returns:
            str: Reporte formateado
        """
        try:
            # Formatear datos principales
            cultivo = user_data['crop'].capitalize()
            area = cls.format_number(user_data['area'])
            ganancia = cls.format_currency(score_data['expected_profit'])
            prestamo = cls.format_currency(score_data['recommended_loan'])
            cuota = cls.format_currency(score_data['monthly_payment'])
            
            # Construir reporte
            report = [
                "📊 *RESUMEN FINANCIERO*\n",
                f"• Cultivo: {cultivo}",
                f"• Área: {area} hectáreas",
                f"• Ganancia potencial: {ganancia}",
                f"• Préstamo disponible: {prestamo}",
                f"• Cuota mensual: {cuota}/mes"
            ]
            
            return "\n".join(report)
            
        except Exception as e:
            return (
                "❌ Error generando reporte\n\n"
                "Por favor contacta a soporte técnico."
            )

# Instancia global
report_generator = FinancialReport()
