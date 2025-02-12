import json
from datetime import datetime
from collections import defaultdict
import os

def clean_maga_data():
    # Obtener la ruta absoluta del directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    # Leer el archivo JSON original
    input_file = os.path.join(root_dir, 'maga_data.json')
    output_file = os.path.join(root_dir, 'maga_data_clean.json')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Diccionario para almacenar el último precio de cada producto
    latest_prices = defaultdict(lambda: {
        'fecha': '2000-01-01',
        'precio': None
    })
    
    # Campos que queremos mantener
    keep_fields = ['Mercado', 'Producto', 'Medida', 'Moneda', 'Precio']
    
    # Procesar cada registro
    for record in data:
        producto = record.get('Producto')
        if not producto:
            continue
            
        try:
            fecha = datetime.strptime(record.get('Fecha', ''), '%d/%m/%Y')
            fecha_str = fecha.strftime('%Y-%m-%d')
            
            # Si este producto tiene una fecha más reciente, actualizamos
            if fecha_str > latest_prices[producto]['fecha']:
                latest_prices[producto] = {
                    'fecha': fecha_str,
                    'data': {k: record.get(k) for k in keep_fields}
                }
        except (ValueError, TypeError):
            continue
    
    # Crear lista final solo con los precios más recientes
    cleaned_data = [
        {
            'Fecha': data['fecha'],
            **data['data']
        }
        for producto, data in latest_prices.items()
        if data['data'].get('Precio') is not None
    ]
    
    # Ordenar por producto
    cleaned_data.sort(key=lambda x: x['Producto'])
    
    # Guardar el archivo limpio
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    print(f"Se procesaron {len(data)} registros")
    print(f"Se guardaron {len(cleaned_data)} productos únicos")
    print(f"Archivo guardado en: {output_file}")

if __name__ == '__main__':
    clean_maga_data()
