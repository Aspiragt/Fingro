"""
Utilidades para formatear moneda
"""

def format_currency(amount: float) -> str:
    """
    Formatea un monto en quetzales
    """
    return f"Q{amount:,.2f}"
