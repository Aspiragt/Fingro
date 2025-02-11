"""
Módulo para manejar solicitudes de préstamo
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LoanApplication:
    """Solicitud de préstamo"""
    applicant_name: str
    applicant_phone: str
    applicant_dpi: str
    crop_name: str
    area_ha: float
    loan_amount: float
    monthly_payment: float
    expected_revenue: float
    expected_profit: float
    application_date: datetime
    status: str = "pending"  # pending, approved, rejected
    
async def start_loan_application(
    crop_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Inicia el proceso de solicitud de préstamo
    Args:
        crop_analysis: Análisis del cultivo
    Returns:
        Dict con información necesaria para la solicitud
    """
    analysis = crop_analysis['financial_analysis']
    
    return {
        'crop_name': crop_analysis['crop_name'],
        'area_ha': crop_analysis['area_ha'],
        'loan_amount': analysis['total_costs'],
        'monthly_payment': (analysis['total_costs'] * 1.15) / 12,  # 15% anual
        'expected_revenue': analysis['expected_revenue'],
        'expected_profit': analysis['expected_profit'],
        'required_fields': [
            {
                'field': 'applicant_name',
                'description': 'Tu nombre completo',
                'type': 'text'
            },
            {
                'field': 'applicant_phone',
                'description': 'Tu número de teléfono',
                'type': 'phone'
            },
            {
                'field': 'applicant_dpi',
                'description': 'Tu número de DPI',
                'type': 'dpi'
            }
        ]
    }

async def submit_loan_application(
    application_data: Dict[str, Any]
) -> Optional[LoanApplication]:
    """
    Envía la solicitud de préstamo
    Args:
        application_data: Datos de la solicitud
    Returns:
        LoanApplication si se creó exitosamente
    """
    try:
        # Aquí iría la lógica para guardar en base de datos
        # y notificar al equipo de FinGro
        
        application = LoanApplication(
            applicant_name=application_data['applicant_name'],
            applicant_phone=application_data['applicant_phone'],
            applicant_dpi=application_data['applicant_dpi'],
            crop_name=application_data['crop_name'],
            area_ha=application_data['area_ha'],
            loan_amount=application_data['loan_amount'],
            monthly_payment=application_data['monthly_payment'],
            expected_revenue=application_data['expected_revenue'],
            expected_profit=application_data['expected_profit'],
            application_date=datetime.now()
        )
        
        # TODO: Guardar en base de datos
        # TODO: Notificar al equipo de FinGro
        
        return application
        
    except Exception as e:
        logger.error(f"Error creando solicitud: {str(e)}", exc_info=True)
        return None
