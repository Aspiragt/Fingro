"""
Script para convertir el CSV de MAGA a un formato JSON estructurado
"""
import csv
import json
import os
from datetime import datetime
from collections import defaultdict

def convert_csv_to_json():
    # Obtener rutas
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    input_file = os.path.join(root_dir, 'maga_precios.csv')
    output_file = os.path.join(root_dir, 'maga_data.json')
    
    # Diccionario para almacenar el último precio de cada producto
    latest_prices = defaultdict(lambda: {
        'fecha': '2000-01-01',
        'precio': None
    })
    
    # Leer CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Leyendo {len(rows)} registros del CSV...")
    
    # Procesar cada fila
    for row in rows:
        try:
            producto = row.get('Producto', '').strip()
            if not producto:
                continue
                
            # La fecha ya viene en formato YYYY-MM-DD
            fecha_str = row.get('Fecha', '')
            
            # Convertir precio a número
            precio_str = row.get('Precio', '0').replace('Q', '').replace(',', '')
            if not precio_str:
                continue
                
            precio = float(precio_str)
            
            # Si este producto tiene una fecha más reciente, actualizamos
            if fecha_str > latest_prices[producto]['fecha']:
                latest_prices[producto] = {
                    'fecha': fecha_str,
                    'precio': precio,
                    'mercado': row.get('Mercado', ''),
                    'medida': row.get('Medida', ''),
                    'moneda': 'GTQ'
                }
        except (ValueError, TypeError) as e:
            print(f"Error procesando fila: {row}")
            print(f"Error: {str(e)}")
            continue
    
    # Crear lista final
    precios = [
        {
            'Producto': producto,
            'Fecha': data['fecha'],
            'Precio': data['precio'],
            'Mercado': data['mercado'],
            'Medida': data['medida'],
            'Moneda': data['moneda']
        }
        for producto, data in latest_prices.items()
        if data['precio'] is not None
    ]
    
    # Ordenar por producto
    precios.sort(key=lambda x: x['Producto'])
    
    # Guardar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(precios, f, ensure_ascii=False, indent=2)
    
    print(f"Se procesaron {len(rows)} registros")
    print(f"Se guardaron {len(precios)} productos únicos")
    print(f"Archivo guardado en: {output_file}")
    
    # Mostrar algunos ejemplos
    print("\nEjemplos de precios:")
    for precio in precios[:5]:
        print(f"{precio['Producto']}: Q{precio['Precio']} por {precio['Medida']}")

if __name__ == '__main__':
    convert_csv_to_json()
