"""
Modelo para solicitudes de préstamo agrícola

Este módulo define la estructura de datos para las solicitudes
de préstamo agrícola procesadas por FinGro.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

class LoanStatus(str, Enum):
    """Estado de la solicitud de préstamo"""
    PENDING = "PENDIENTE"
    APPROVED = "APROBADO"
    EVALUATION = "EVALUACIÓN"
    REJECTED = "RECHAZADO"
    DISBURSED = "DESEMBOLSADO"
    COMPLETED = "COMPLETADO"
    CANCELLED = "CANCELADO"

class LoanPurpose(str, Enum):
    """Propósito del préstamo"""
    SEEDS = "SEMILLAS"
    FERTILIZER = "FERTILIZANTE"
    IRRIGATION = "SISTEMA_RIEGO"
    EQUIPMENT = "EQUIPO"
    LABOR = "MANO_OBRA"
    LAND = "TERRENO"
    OTHER = "OTRO"

class LoanApplicationModel(BaseModel):
    """Modelo de solicitud de préstamo agrícola"""
    id: str = Field(..., description="Identificador único de la solicitud")
    user_id: str = Field(..., description="ID del usuario solicitante")
    created_at: datetime = Field(default_factory=datetime.now, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    # Datos del préstamo
    amount: float = Field(..., gt=0, description="Monto del préstamo en quetzales")
    term_months: int = Field(..., gt=0, description="Plazo en meses")
    monthly_payment: float = Field(..., gt=0, description="Cuota mensual estimada")
    interest_rate: float = Field(0.12, ge=0, le=1, description="Tasa de interés anual")
    
    # Datos del cultivo/proyecto
    crop: str = Field(..., description="Cultivo principal")
    area: float = Field(..., gt=0, description="Área en hectáreas")
    irrigation: str = Field(..., description="Sistema de riego")
    location: str = Field(..., description="Departamento")
    channel: str = Field(..., description="Canal de comercialización")
    
    # Propósito y uso
    purpose: LoanPurpose = Field(..., description="Propósito principal del préstamo")
    purpose_detail: Optional[str] = Field(None, description="Detalle adicional sobre el propósito")
    
    # Estado y evaluación
    status: LoanStatus = Field(default=LoanStatus.PENDING, description="Estado actual")
    fingro_score: int = Field(..., ge=0, le=1000, description="Puntaje FinGro")
    score_details: Dict[str, Any] = Field(default_factory=dict, description="Detalles del puntaje")
    approval_date: Optional[datetime] = Field(None, description="Fecha de aprobación")
    rejection_reason: Optional[str] = Field(None, description="Razón de rechazo si aplica")
    
    # Documentos y referencias
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de documentos adjuntos")
    notes: Optional[str] = Field(None, description="Notas adicionales")
    
    @validator('irrigation')
    def validate_irrigation(cls, v):
        """Valida que el sistema de riego sea válido"""
        valid_systems = ['goteo', 'aspersion', 'gravedad', 'temporal']
        if v.lower() not in valid_systems:
            raise ValueError(f"Sistema de riego no válido. Debe ser uno de: {valid_systems}")
        return v.lower()
    
    @validator('channel')
    def validate_channel(cls, v):
        """Valida que el canal de comercialización sea válido"""
        valid_channels = ['exportacion', 'cooperativa', 'mayorista', 'local']
        if v.lower() not in valid_channels:
            raise ValueError(f"Canal no válido. Debe ser uno de: {valid_channels}")
        return v.lower()
    
    def calculate_total_repayment(self) -> float:
        """Calcula el monto total a pagar"""
        return self.monthly_payment * self.term_months
    
    def is_eligible_for_automatic_approval(self) -> bool:
        """Determina si el préstamo es elegible para aprobación automática"""
        return self.fingro_score >= 800 and self.amount <= 10000
    
    def get_status_message(self) -> str:
        """Obtiene mensaje para el usuario según el estado"""
        if self.status == LoanStatus.PENDING:
            return ("Su solicitud está pendiente de revisión. Le notificaremos "
                    "cuando sea procesada. 🕒")
                    
        elif self.status == LoanStatus.APPROVED:
            return ("¡Felicidades! Su préstamo ha sido aprobado. Pronto nos "
                    "contactaremos para coordinar el desembolso. 🎉")
                    
        elif self.status == LoanStatus.EVALUATION:
            return ("Su solicitud está en evaluación. Un asesor se comunicará con "
                    "usted para verificar algunos datos adicionales. 🔍")
                    
        elif self.status == LoanStatus.REJECTED:
            reason = self.rejection_reason or "No cumple con los requisitos mínimos"
            return (f"Lo sentimos, su solicitud no fue aprobada. Motivo: {reason}. "
                    "Puede intentarlo nuevamente en 3 meses. 🌱")
                    
        elif self.status == LoanStatus.DISBURSED:
            return ("Su préstamo ha sido desembolsado. Recuerde realizar sus pagos "
                    "a tiempo para mantener un buen historial crediticio. 💰")
                    
        elif self.status == LoanStatus.COMPLETED:
            return ("¡Felicidades! Ha completado sus pagos exitosamente. Ahora es "
                    "elegible para préstamos de mayor monto. 🏆")
                    
        else:
            return ("El estado actual de su préstamo es: " + self.status)
