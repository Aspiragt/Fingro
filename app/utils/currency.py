"""
Utilidades para formatear moneda
"""

def format_currency(amount: float) -> str:
    """
    Formatea un monto en quetzales
    
    Args:
        amount: Monto a formatear
        
    Returns:
        str: Monto formateado como Q1,234.56
    """
    try:
        return f"Q{amount:,.2f}"
    except (TypeError, ValueError):
        return "Q0.00"
