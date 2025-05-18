#!/usr/bin/env python3
"""
Script para automatizar la optimización del proyecto.
Ejecuta varias tareas para limpiar código obsoleto y optimizar el proyecto.
"""
import os
import shutil
import re
import pandas as pd

def main():
    print("Iniciando optimización del proyecto...")
    
    # 1. Eliminar archivos obsoletos
    print("Eliminando archivos obsoletos...")
    obsolete_files = [
        'energia_app/templates/macros.html',
        'energia_app/static/js/building_charts.js',
        'energia_app/static/js/charts.js',
    ]
    
    for file_path in obsolete_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"  - Eliminado: {file_path}")
    
    # 2. Consolidar archivos CSV
    print("Consolidando archivos CSV...")
    try:
        csv_files = [
            'energia_app/data/energy_data.csv',
            'energia_app/data/energy_data_template.csv',
            'energia_app/data/synthetic_energy_data.csv'
        ]
        
        # Verificar si los archivos existen
        existing_files = [f for f in csv_files if os.path.exists(f)]
        
        if existing_files:
            # Crear una lista de DataFrames
            dfs = [pd.read_csv(f) for f in existing_files]
            
            # Concatenar y eliminar duplicados
            df_combined = pd.concat(dfs).drop_duplicates()
            
            # Guardar el archivo consolidado
            output_path = 'energia_app/data/consolidated_energy_data.csv'
            df_combined.to_csv(output_path, index=False)
            print(f"  - Creado archivo consolidado: {output_path}")
        else:
            print("  - No se encontraron archivos CSV para consolidar")
    
    except Exception as e:
        print(f"  - Error al consolidar archivos CSV: {str(e)}")
    
    print("Optimización completada.")

if __name__ == "__main__":
    main()