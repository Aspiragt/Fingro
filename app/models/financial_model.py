"""
Módulo para análisis financiero de proyectos agrícolas
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging
from app.external_apis.maga import maga_api, CanalComercializacion

logger = logging.getLogger(__name__)

@dataclass
class CostosCultivo:
    """Costos base por hectárea para diferentes cultivos"""
    preparacion_suelo: float
    semilla: float
    fertilizantes: float
    pesticidas: float
    mano_obra: float
    cosecha: float
    otros: float

class FinancialModel:
    """Modelo financiero para proyectos agrícolas"""
    
    def __init__(self):
        """Inicializa el modelo financiero"""
        
        # Costos base por hectárea para diferentes cultivos
        self.costos_cultivos = {
            'maiz': CostosCultivo(
                preparacion_suelo=2000,
                semilla=1500,
                fertilizantes=4000,
                pesticidas=2000,
                mano_obra=6000,
                cosecha=3000,
                otros=1500
            ),
            'frijol': CostosCultivo(
                preparacion_suelo=2000,
                semilla=2000,
                fertilizantes=3500,
                pesticidas=1500,
                mano_obra=5000,
                cosecha=2500,
                otros=1500
            ),
            'papa': CostosCultivo(
                preparacion_suelo=3000,
                semilla=6000,
                fertilizantes=5000,
                pesticidas=3000,
                mano_obra=8000,
                cosecha=4000,
                otros=2000
            ),
            'tomate': CostosCultivo(
                preparacion_suelo=4000,    # Preparación más intensiva
                semilla=8000,             # Plántulas de calidad
                fertilizantes=12000,      # Fertilización intensiva
                pesticidas=6000,          # Control de plagas
                mano_obra=15000,          # Mano de obra especializada
                cosecha=5000,             # Cosecha cuidadosa
                otros=3000                # Tutoreo, materiales, etc.
            )
        }
        
        # Factor de rendimiento según sistema de riego
        self.irrigation_yield_factor = {
            'gravedad': 0.9,    # -10% por menor eficiencia
            'aspersion': 1.1,   # +10% por mejor distribución
            'goteo': 1.3,       # +30% por eficiencia óptima
            'ninguno': 0.6      # -40% por depender de lluvia
        }
        
        # Rendimiento base por hectárea (quintales)
        self.base_yield = {
            'maiz': 80,
            'frijol': 35,
            'papa': 450,
            'tomate': 800,      # 800qq/ha es el rendimiento promedio
            'cafe': 40,
            'chile': 350,
            'cebolla': 600,
            'repollo': 700,
            'arveja': 200,
            'aguacate': 300,
            'platano': 500,
            'limon': 400,
            'zanahoria': 550,
            'brocoli': 400
        }
        
        # Factores de riesgo por canal
        self.risk_factors = {
            CanalComercializacion.EXPORTACION: 0.8,  # Mayor riesgo por estándares
            CanalComercializacion.COOPERATIVA: 0.4,  # Menor riesgo por apoyo
            CanalComercializacion.MAYORISTA: 0.6,    # Riesgo moderado
            CanalComercializacion.MERCADO_LOCAL: 0.5 # Riesgo moderado-bajo
        }
        
        # Factores de conversión a quintales
        self.conversion_factors = {
            'Quintal': 1.0,  # Base unit
            'Caja (45-50 lb)': 0.5,  # 1 quintal = 2 cajas de tomate
            'Red (90 - 100 unidades) (64.55 kg)': 1.42,  # 64.55kg ≈ 142lb ≈ 1.42qq
            'Caja (7 kg)': 0.154,  # 7kg ≈ 15.4lb ≈ 0.154qq
            'Caja (35 - 40 unidades)': 0.4,  # Aprox 40lb ≈ 0.4qq
            'Red (90 - 100 unidades) (24 kg)': 0.528,  # 24kg ≈ 52.8lb ≈ 0.528qq
            'Costal (40 lb)': 0.4,  # 40lb = 0.4qq
            'Costal (100 lb)': 1.0,  # 100lb = 1qq
            'Libra': 0.01,  # 1lb = 0.01qq
            'Kilogramo': 0.022,  # 1kg ≈ 2.2lb ≈ 0.022qq
            'Docena': None,  # Requiere peso específico del producto
            'Mazo (20 trenzas)': None  # Requiere peso específico del producto
        }
        
        # Peso por unidad para productos específicos (en libras)
        self.peso_por_unidad = {
            'repollo': 5,  # 5 lb por unidad
            'cebolla': 0.5,  # 0.5 lb por unidad
            'chile': 0.25,  # 0.25 lb por unidad
            'tomate': 0.5,  # 0.5 lb por unidad
            'aguacate': 1,  # 1 lb por unidad
        }
    
    def _get_costos_cultivo(self, cultivo: str, area: float) -> Dict[str, float]:
        """
        Calcula los costos para un cultivo y área específicos
        
        Args:
            cultivo: Nombre del cultivo
            area: Área en hectáreas
            
        Returns:
            Dict[str, float]: Desglose de costos
        """
        # Obtener costos base o usar un cultivo similar
        costos_base = self.costos_cultivos.get(cultivo)
        if not costos_base:
            # Usar costos del maíz como base
            costos_base = self.costos_cultivos['maiz']
            logger.warning(f"Usando costos base de maíz para {cultivo}")
        
        # Calcular costos totales
        return {
            'preparacion_suelo': costos_base.preparacion_suelo * area,
            'semilla': costos_base.semilla * area,
            'fertilizantes': costos_base.fertilizantes * area,
            'pesticidas': costos_base.pesticidas * area,
            'mano_obra': costos_base.mano_obra * area,
            'cosecha': costos_base.cosecha * area,
            'otros': costos_base.otros * area
        }
    
    def _get_rendimiento_esperado(self, cultivo: str, area: float, riego: str) -> float:
        """
        Calcula el rendimiento esperado en quintales
        
        Args:
            cultivo: Nombre del cultivo
            area: Área en hectáreas
            riego: Sistema de riego
            
        Returns:
            float: Rendimiento esperado en quintales
        """
        # Obtener rendimiento base
        base = self.base_yield.get(cultivo, 100)  # 100qq/ha por defecto
        
        # Aplicar factor de riego
        factor = self.irrigation_yield_factor.get(riego, 1.0)
        
        return base * area * factor
    
    def _calculate_risk_score(self, cultivo: str, canal: str, riego: str) -> float:
        """
        Calcula el nivel de riesgo del proyecto
        
        Args:
            cultivo: Nombre del cultivo
            canal: Canal de comercialización
            riego: Sistema de riego
            
        Returns:
            float: Puntaje de riesgo (0-1, donde 1 es más riesgoso)
        """
        # Riesgo base por canal
        risk = self.risk_factors.get(canal, 0.6)
        
        # Ajustar por sistema de riego
        if riego == 'ninguno':
            risk += 0.2
        elif riego in ['goteo', 'aspersion']:
            risk -= 0.1
        
        # Ajustar por tipo de cultivo
        if cultivo in maga_api.export_crops:
            risk += 0.1  # Cultivos de exportación tienen más riesgo
        if cultivo in maga_api.cooperative_crops:
            risk -= 0.1  # Cultivos de cooperativa son más estables
            
        # Mantener el riesgo entre 0 y 1
        return max(0.0, min(1.0, risk))
    
    def _convert_to_quintales(self, precio: float, medida: str, cultivo: str = None) -> float:
        """
        Convierte el precio por unidad de medida a precio por quintal
        
        Args:
            precio: Precio en la unidad original
            medida: Unidad de medida original
            cultivo: Nombre del cultivo (necesario para algunas conversiones)
            
        Returns:
            float: Precio por quintal
        """
        try:
            # Si ya está en quintales, retornar directo
            if medida == 'Quintal':
                return precio
                
            # Obtener factor de conversión
            factor = self.conversion_factors.get(medida)
            
            # Si no hay factor directo pero es una medida por unidad
            if factor is None and medida in ['Docena']:
                if cultivo and cultivo in self.peso_por_unidad:
                    peso_lb = self.peso_por_unidad[cultivo]
                    if medida == 'Docena':
                        factor = (peso_lb * 12) / 100  # 12 unidades / 100 lb por quintal
                
            if factor is None:
                logger.warning(f"No se pudo convertir medida {medida} para {cultivo}")
                return precio
                
            return precio / factor
            
        except Exception as e:
            logger.error(f"Error convirtiendo precio: {str(e)}")
            return precio
    
    async def analyze_project(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza un proyecto agrícola y genera reporte financiero
        
        Args:
            user_data: Datos del usuario y proyecto
            
        Returns:
            Dict[str, Any]: Análisis financiero
        """
        try:
            # Extraer datos
            cultivo = user_data['crop'].lower()
            area = float(user_data['area'])
            riego = user_data['irrigation'].lower()
            canal = user_data.get('commercialization', CanalComercializacion.MAYORISTA)
            
            # 1. Obtener precios
            price_data = await maga_api.get_precio_cultivo(cultivo, canal)
            if not price_data or 'precio' not in price_data:
                logger.error(f"Error obteniendo precio para {cultivo}")
                return None
                
            precio_original = price_data['precio']
            medida_original = price_data.get('medida', 'Quintal')
            
            # Convertir precio a quintales
            precio_quintal = self._convert_to_quintales(
                precio_original, 
                medida_original,
                cultivo
            )
            
            # 2. Calcular costos
            costos = self._get_costos_cultivo(cultivo, area)
            costos_siembra = sum(costos.values())
            
            # 3. Calcular rendimiento
            rendimiento = self._get_rendimiento_esperado(cultivo, area, riego)
            
            # 4. Calcular ingresos
            ingresos = rendimiento * precio_quintal
            
            # 5. Calcular rentabilidad
            utilidad = ingresos - costos_siembra
            utilidad_por_ha = utilidad / area
            
            # 6. Calcular riesgo
            risk_score = self._calculate_risk_score(cultivo, canal, riego)
            
            # 7. Preparar respuesta
            return {
                'cultivo': cultivo,
                'area': area,
                'rendimiento': rendimiento,
                'rendimiento_por_ha': rendimiento / area,
                'precio_original': precio_original,
                'medida_original': medida_original,
                'precio_quintal': precio_quintal,
                'ingresos_totales': ingresos,
                'costos_siembra': costos_siembra,
                'costos_por_ha': costos_siembra / area,
                'utilidad': utilidad,
                'utilidad_por_ha': utilidad_por_ha,
                'roi': (utilidad / costos_siembra) * 100,
                'riesgo': risk_score,
                'desglose_costos': costos
            }
            
        except Exception as e:
            logger.error(f"Error analizando proyecto: {str(e)}")
            return None

# Instancia global
financial_model = FinancialModel()
