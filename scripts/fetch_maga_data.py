"""
Script para obtener datos de precios del MAGA y guardarlos en un archivo JSON
"""
import asyncio
import json
import os
from app.external_apis.maga_precios import maga_precios_client

async def fetch_maga_data():
    # Lista de cultivos a buscar
    cultivos = [
        'tomate',
        'papa',
        'maiz',
        'frijol',
        'cafe',
        'chile',
        'cebolla',
        'repollo',
        'arveja',
        'camote'
    ]
    
    # Obtener datos para cada cultivo
    all_data = []
    
    for cultivo in cultivos:
        print(f"Obteniendo datos para {cultivo}...")
        data = await maga_precios_client._get_price_data(cultivo)
        if data:
            all_data.append(data)
    
    # Guardar datos en archivo JSON
    output_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'maga_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"Se guardaron datos de {len(all_data)} cultivos en {output_file}")

if __name__ == '__main__':
    asyncio.run(fetch_maga_data())
