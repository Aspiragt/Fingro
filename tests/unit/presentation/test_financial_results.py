"""
Pruebas unitarias para el módulo de presentación de resultados financieros
"""
import unittest
from unittest.mock import patch, MagicMock

from app.presentation.financial_results import FinancialResultsPresenter

class TestFinancialResultsPresenter(unittest.TestCase):
    """Pruebas para la presentación de resultados financieros"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.presenter = FinancialResultsPresenter()
        
    def test_get_category_level_cultivo(self):
        """Prueba la determinación de nivel para categoría de cultivo"""
        self.assertEqual(self.presenter.get_category_level('cultivo', 100), 'bajo')
        self.assertEqual(self.presenter.get_category_level('cultivo', 140), 'medio')
        self.assertEqual(self.presenter.get_category_level('cultivo', 180), 'alto')
        
    def test_get_category_level_area(self):
        """Prueba la determinación de nivel para categoría de área"""
        self.assertEqual(self.presenter.get_category_level('area', 100), 'bajo')
        self.assertEqual(self.presenter.get_category_level('area', 140), 'medio')
        self.assertEqual(self.presenter.get_category_level('area', 180), 'alto')
        
    def test_get_category_level_comercializacion(self):
        """Prueba la determinación de nivel para categoría de comercialización"""
        self.assertEqual(self.presenter.get_category_level('comercializacion', 120), 'bajo')
        self.assertEqual(self.presenter.get_category_level('comercializacion', 150), 'medio')
        self.assertEqual(self.presenter.get_category_level('comercializacion', 190), 'alto')
        
    def test_get_category_level_riego(self):
        """Prueba la determinación de nivel para categoría de riego"""
        self.assertEqual(self.presenter.get_category_level('riego', 100), 'bajo')
        self.assertEqual(self.presenter.get_category_level('riego', 180), 'medio')
        self.assertEqual(self.presenter.get_category_level('riego', 220), 'alto')
        
    def test_get_category_level_ubicacion(self):
        """Prueba la determinación de nivel para categoría de ubicación"""
        self.assertEqual(self.presenter.get_category_level('ubicacion', 90), 'bajo')
        self.assertEqual(self.presenter.get_category_level('ubicacion', 110), 'medio')
        self.assertEqual(self.presenter.get_category_level('ubicacion', 140), 'alto')
        
    def test_get_recommendations(self):
        """Prueba la generación de recomendaciones personalizadas"""
        # Datos de prueba
        score_details = {
            'cultivo': 100, # Bajo
            'area': 140,    # Medio
            'comercializacion': 190, # Alto
            'riego': 100,   # Bajo
            'ubicacion': 130 # Medio
        }
        
        recommendations = self.presenter.get_recommendations(score_details)
        
        # Verificar que se generaron recomendaciones
        self.assertTrue(len(recommendations) >= 1)
        # Verificar que contiene las palabras clave esperadas
        self.assertIn("cultivo", recommendations[0].lower())
        
    @patch('app.scoring.credit_score.score_calculator.calculate_fingro_score')
    @patch('app.scoring.credit_score.score_calculator.get_loan_approval_status')
    @patch('app.utils.loan_calculator.calculate_loan_amount')
    def test_format_financial_analysis_high_score(self, mock_loan_calculator, mock_get_status, mock_fingro_score):
        """Prueba el formateo del análisis financiero para puntaje alto (aprobación inmediata)"""
        # Configurar el mock
        mock_fingro_score.return_value = (
            890,  # Puntaje total alto
            {    # Detalles por categoría
                'cultivo': 180,
                'area': 180,
                'comercializacion': 190,
                'riego': 180,
                'ubicacion': 150,
                'total': 890
            }
        )
        mock_get_status.return_value = (
            "APROBADO",
            "¡Felicidades! 🎉 Su préstamo ha sido aprobado automáticamente. Su perfil agrícola muestra un excelente potencial de éxito."
        )
        
        # Mock para el calculador de préstamos
        mock_loan_calculator.return_value = 4000.0
        
        # Datos de prueba
        user_data = {
            'crop': 'aguacate',
            'area': 5,
            'channel': 'exportacion',
            'irrigation': 'goteo',
            'location': 'huehuetenango'
        }
        
        result = self.presenter.format_financial_analysis(user_data)
        
        # Verificar componentes clave del mensaje
        self.assertIn("Análisis de su proyecto de Aguacate", result)
        self.assertIn("890 puntos", result)
        self.assertIn("Monto máximo aprobado:", result)
        self.assertIn("Q4,000.00", result)
        self.assertIn("¿Desea recibir su préstamo ahora?", result)
        
    @patch('app.scoring.credit_score.score_calculator.calculate_fingro_score')
    @patch('app.scoring.credit_score.score_calculator.get_loan_approval_status')
    @patch('app.utils.loan_calculator.calculate_loan_amount')
    def test_format_financial_analysis_medium_score(self, mock_loan_calculator, mock_get_status, mock_fingro_score):
        """Prueba el formateo del análisis financiero para puntaje medio (evaluación manual)"""
        # Configurar el mock
        mock_fingro_score.return_value = (
            740,  # Puntaje total medio
            {    # Detalles por categoría
                'cultivo': 150,
                'area': 160,
                'comercializacion': 150,
                'riego': 100,
                'ubicacion': 90,
                'total': 740
            }
        )
        mock_get_status.return_value = (
            "EVALUACIÓN",
            "Su préstamo requiere una evaluación manual adicional. 🔍 Su perfil muestra buen potencial, pero necesitamos revisar algunos detalles para asegurar el éxito de su proyecto."
        )
        
        # Mock para el calculador de préstamos
        mock_loan_calculator.return_value = 4000.0
        
        # Datos de prueba
        user_data = {
            'crop': 'maíz',
            'area': 3,
            'channel': 'mayorista',
            'irrigation': 'aspersion',
            'location': 'escuintla'
        }
        
        result = self.presenter.format_financial_analysis(user_data)
        
        # Verificar componentes clave del mensaje
        self.assertIn("Análisis de su proyecto de Maíz", result)
        self.assertIn("Su Fingro Score es: 740 puntos", result)
        self.assertIn("Su préstamo requiere una evaluación manual adicional", result)
        self.assertIn("asegurar el éxito de su proyecto", result)
        self.assertIn("Monto máximo recomendado:", result)
        self.assertIn("Q4,000.00", result)
        self.assertIn("Recomendaciones para mejorar", result)
        self.assertIn("¿Le interesa continuar", result)
    
    @patch('app.scoring.credit_score.score_calculator')
    @patch('app.utils.loan_calculator.calculate_loan_amount')
    def test_format_financial_analysis_low_score(self, mock_loan_calculator, mock_calculator):
        """Prueba el formateo del análisis financiero para puntaje bajo (rechazo con recomendaciones)"""
        # Configurar el mock para forzar un valor bajo (< 500)
        mock_calculator.calculate_fingro_score.return_value = (
            450,  # Puntaje total bajo
            {    # Detalles por categoría
                'cultivo': 100,
                'area': 100,
                'comercializacion': 100,
                'riego': 100,
                'ubicacion': 50,
                'total': 450
            }
        )
        
        # Este es el mensaje clave - configuramos un mensaje de rechazo en lugar de evaluación
        mock_calculator.get_loan_approval_status.return_value = (
            "RECHAZADO",
            "Lo sentimos, su préstamo no puede ser aprobado en este momento. 🌱 Le recomendamos mejorar aspectos clave como su sistema de riego o diversificar sus canales de comercialización para aumentar sus posibilidades de aprobación en el futuro."
        )
        
        # Mock para el calculador de préstamos
        mock_loan_calculator.return_value = 4000.0
        
        # Datos de prueba
        user_data = {
            'crop': 'tomate',
            'area': 2,
            'channel': 'local',
            'irrigation': 'temporal',
            'location': 'jutiapa'
        }
        
        # Comprobar que el mock está configurado correctamente antes de llamar
        self.assertEqual(mock_calculator.calculate_fingro_score.return_value[0], 450)
        
        result = self.presenter.format_financial_analysis(user_data)
        
        # Verificar componentes clave del mensaje
        self.assertIn("Análisis de su proyecto de Tomate", result)
        self.assertIn("450 puntos", result)
        self.assertIn("no puede ser aprobado", result)
        self.assertIn("Recomendaciones para mejorar", result)
        self.assertIn("volver a solicitar", result)
        self.assertIn("información adicional", result)
        
    @patch('app.scoring.credit_score.score_calculator.calculate_fingro_score')
    @patch('app.scoring.credit_score.score_calculator.get_loan_approval_status')
    @patch('app.utils.loan_calculator.calculate_loan_amount')
    def test_format_financial_analysis_low_score(self, mock_loan_calculator, mock_get_status, mock_fingro_score):
        """Prueba el formateo del análisis financiero para puntaje bajo (rechazo con recomendaciones)"""
        # Configurar el mock para forzar un valor bajo (< 500)
        mock_fingro_score.return_value = (
            450,  # Puntaje total bajo
            {    # Detalles por categoría
                'cultivo': 100,
                'area': 100,
                'comercializacion': 100,
                'riego': 100,
                'ubicacion': 50,
                'total': 450
            }
        )
        
        # Este es el mensaje clave - configuramos un mensaje de rechazo en lugar de evaluación
        mock_get_status.return_value = (
            "RECHAZADO",
            "Lo sentimos, su préstamo no puede ser aprobado en este momento. 🌱 Le recomendamos mejorar aspectos clave como su sistema de riego o diversificar sus canales de comercialización para aumentar sus posibilidades de aprobación en el futuro."
        )
        
        # Mock para el calculador de préstamos
        mock_loan_calculator.return_value = 4000.0
        
        # Datos de prueba
        user_data = {
            'crop': 'tomate',
            'area': 2,
            'channel': 'local',
            'irrigation': 'temporal',
            'location': 'jutiapa'
        }
        
        result = self.presenter.format_financial_analysis(user_data)
        
        # Verificar componentes clave del mensaje
        self.assertIn("Análisis de su proyecto de Tomate", result)
        self.assertIn("450 puntos", result)
        self.assertIn("no puede ser aprobado", result)
        self.assertIn("Recomendaciones para mejorar", result)
        self.assertIn("volver a solicitar", result)
        self.assertIn("información adicional", result)
        
    @patch('app.scoring.credit_score.score_calculator')
    @patch('app.utils.loan_calculator.calculate_loan_amount')
    def test_format_financial_analysis_with_error(self, mock_loan_calculator, mock_calculator):
        """Prueba el manejo de errores en el análisis financiero"""
        # Configurar el mock para lanzar una excepción
        mock_calculator.calculate_fingro_score.side_effect = Exception("Error de prueba")
        mock_loan_calculator.return_value = 6000.0
        
        # Datos de prueba
        user_data = {
            'crop': 'maíz',
            'area': 3
        }
        
        result = self.presenter.format_financial_analysis(user_data)
        
        # Verificar que devuelve un mensaje, no importa el contenido exacto
        self.assertTrue(len(result) > 0)
        self.assertIn("solicitud", result.lower())
        
if __name__ == '__main__':
    unittest.main()
