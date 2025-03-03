"""
Utilidades para cálculo de préstamos agrícolas
"""

def calculate_loan_amount(area_ha: float) -> float:
    """
    Calcula el monto del préstamo basado en las hectáreas
    según los montos fijos totales de FinGro
    
    Args:
        area_ha: Área en hectáreas
        
    Returns:
        float: Monto del préstamo en quetzales
    """
    if area_ha <= 0:
        return 0
        
    # Montos fijos totales según rango de hectáreas
    if area_ha <= 10:
        return 4000
    elif area_ha <= 15:
        return 8000
    else:
        return 16000

def calculate_monthly_payment(loan_amount: float) -> float:
    """
    Calcula el pago mensual para un préstamo
    
    Args:
        loan_amount: Monto del préstamo
        
    Returns:
        float: Pago mensual estimado
    """
    # Cálculo simple con tasa del 12% anual a 9 meses
    annual_rate = 0.12
    monthly_rate = annual_rate / 12
    term_months = 9
    
    # Fórmula de amortización
    if monthly_rate == 0:
        return loan_amount / term_months
        
    payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    return payment
