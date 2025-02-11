"""
Módulo para generar reportes simples y fáciles de entender
"""
from typing import Dict, Any
from datetime import datetime

def format_money(amount: float) -> str:
    """Formatea cantidades de dinero en quetzales"""
    return f"Q{amount:,.0f}"

def format_number(num: float) -> str:
    """Formatea números con separadores de miles"""
    return f"{num:,.1f}"

def get_simple_analysis(data: Dict[str, Any]) -> str:
    """
    Genera un reporte simple y fácil de entender
    Args:
        data: Datos del análisis de rentabilidad
    Returns:
        Reporte en formato texto
    """
    if not data:
        return "No se pudo hacer el análisis. Por favor intente de nuevo."
        
    # Extraer datos
    analysis = data['financial_analysis']
    yield_data = data['yield_data']
    
    # Calcular valores por mes
    months = yield_data['growing_time_days'] / 30
    profit_per_month = analysis['expected_profit'] / months
    monthly_payment = (analysis['total_costs'] * 1.15) / 12
    
    # Generar mensaje
    lines = []
    
    # Mensaje principal
    lines.append(f"Para tu siembra de {format_number(data['area_ha'])} hectáreas de {data['crop_name']},")
    lines.append(f"podrías vender tu cosecha en {format_money(analysis['expected_revenue'])}")
    lines.append(f"con un costo de {format_money(analysis['total_costs'])},")
    lines.append(f"obteniendo ganancias de {format_money(analysis['expected_profit'])}.")
    lines.append("")
    lines.append("¿Te gustaría aplicar a un crédito FinGro para tu plantación?")
    lines.append("")
    lines.append("Escribe 'SI' para aplicar ahora mismo.")
    
    return "\n".join(lines)
