#!/usr/bin/env python3
"""
Script para eliminar rutas y funciones redundantes en la aplicación Flask
de predicción de consumo energético tras la simplificación del sistema de datos.

Uso:
- Hacer una copia de seguridad de los archivos antes de ejecutar
- Ejecutar: python cleanup_redundant_code.py
"""

import os
import re
import shutil
from datetime import datetime

# Configuración
APP_PY_PATH = 'app.py'
BACKUP_DIR = 'backups_' + datetime.now().strftime('%Y%m%d_%H%M%S')
DATA_LOADER_PATH = 'energia_app/utils/data_loader.py'
DATA_DIR_PATH = 'energia_app/data'  # Directorio que podría eliminarse si solo contiene CSVs

# Funciones a eliminar de app.py (nombres exactos)
ROUTES_TO_REMOVE = [
    'dataset_management',
    'export_to_dataset',
]

# Patrón para encontrar la definición de una función/ruta
ROUTE_PATTERN = r'@app\.route\([^\)]+\)\s*\n@login_required\s*\ndef\s+({}).*?(?=@app\.route|\Z)'

# Patrones para eliminar configs de directorios de datos
CONFIG_PATTERNS = [
    r"app\.config\['UPLOAD_FOLDER'\]\s*=\s*os\.path\.join\([^)]+\)[^\n]*\n",
    r"app\.config\['MAX_CONTENT_LENGTH'\]\s*=\s*[^\n]*\n",
    r"app\.config\['ALLOWED_EXTENSIONS'\]\s*=\s*[^\n]*\n",
]

# Funciones obsoletas en data_loader.py
DATA_LOADER_FUNCS = [
    'load_csv_dataset',
    'save_dataset',
    'get_dataset_statistics',
]

def create_backup(filename):
    """Crea una copia de seguridad del archivo"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    shutil.copy2(filename, backup_path)
    print(f"Backup creado: {backup_path}")
    return backup_path

def remove_routes_from_app_py():
    """Elimina las rutas redundantes de app.py"""
    if not os.path.exists(APP_PY_PATH):
        print(f"¡Error! No se encontró el archivo {APP_PY_PATH}")
        return False
    
    # Crear backup
    create_backup(APP_PY_PATH)
    
    # Leer el contenido del archivo
    with open(APP_PY_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Contar ocurrencias originales para verificación
    original_routes_count = 0
    for route in ROUTES_TO_REMOVE:
        pattern = ROUTE_PATTERN.format(route)
        matches = re.finditer(pattern, content, re.DOTALL)
        for _ in matches:
            original_routes_count += 1
    
    # Eliminar las rutas
    for route in ROUTES_TO_REMOVE:
        pattern = ROUTE_PATTERN.format(route)
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Eliminar configuraciones relacionadas con directorios de datos
    for pattern in CONFIG_PATTERNS:
        content = re.sub(pattern, '', content)
    
    # Escribir el archivo actualizado
    with open(APP_PY_PATH, 'w', encoding='utf-8') as file:
        file.write(content)
    
    # Verificar eliminación
    removed_count = original_routes_count - sum(1 for route in ROUTES_TO_REMOVE 
                                               for _ in re.finditer(ROUTE_PATTERN.format(route), content, re.DOTALL))
    print(f"Se eliminaron {removed_count} rutas y configuraciones redundantes de {APP_PY_PATH}")
    return True

def clean_data_loader():
    """Limpia o marca como obsoletas las funciones en data_loader.py"""
    if not os.path.exists(DATA_LOADER_PATH):
        print(f"No se encontró el archivo {DATA_LOADER_PATH}. Omitiendo...")
        return False
    
    # Crear backup
    create_backup(DATA_LOADER_PATH)
    
    # Leer el contenido
    with open(DATA_LOADER_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Reemplazar las funciones con comentarios que indiquen su obsolescencia
    for func_name in DATA_LOADER_FUNCS:
        func_pattern = r'def\s+' + func_name + r'\([^\)]*\):.*?(?=def|\Z)'
        replacement = f'''
# OBSOLETO: Esta función ya no se utiliza, use EnergyData.export_to_df() o EnergyData.import_from_df() en su lugar
# def {func_name}(...): ...
'''
        content = re.sub(func_pattern, replacement, content, flags=re.DOTALL)
    
    # Escribir el archivo actualizado
    with open(DATA_LOADER_PATH, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Se marcaron las funciones obsoletas en {DATA_LOADER_PATH}")
    return True

def check_data_directory():
    """Verifica si el directorio de datos contiene solo CSVs y puede ser eliminado"""
    if not os.path.exists(DATA_DIR_PATH):
        print(f"No se encontró el directorio {DATA_DIR_PATH}. Omitiendo...")
        return
    
    # Verificar contenido
    files = os.listdir(DATA_DIR_PATH)
    csv_files = [f for f in files if f.endswith('.csv')]
    non_csv_files = [f for f in files if not f.endswith('.csv')]
    
    print(f"\nEl directorio {DATA_DIR_PATH} contiene:")
    print(f"- {len(csv_files)} archivos CSV")
    print(f"- {len(non_csv_files)} archivos no-CSV")
    
    if non_csv_files:
        print("\n¡ADVERTENCIA! El directorio contiene archivos que no son CSV:")
        for f in non_csv_files:
            print(f"  - {f}")
        print("Se recomienda revisar estos archivos antes de eliminar el directorio.")
    else:
        print("\nEl directorio contiene solo archivos CSV, que ya no son necesarios.")
        
    print("\nRECOMENDACIÓN:")
    if len(files) == 0:
        print(f"El directorio {DATA_DIR_PATH} está vacío y puede ser eliminado con seguridad.")
    elif len(non_csv_files) == 0:
        print(f"El directorio {DATA_DIR_PATH} contiene solo archivos CSV y puede ser eliminado después de respaldar los datos.")
    else:
        print(f"Revise manualmente el directorio {DATA_DIR_PATH} antes de eliminarlo.")

def main():
    """Función principal del script"""
    print("=== Script de limpieza de código redundante ===")
    print(f"Creando copias de seguridad en: {BACKUP_DIR}")
    
    # Eliminar rutas redundantes
    remove_routes_from_app_py()
    
    # Limpiar data_loader.py
    clean_data_loader()
    
    # Verificar directorio de datos
    check_data_directory()
    
    print("\n=== Limpieza completada ===")
    print(f"Se han creado copias de seguridad en: {BACKUP_DIR}")
    print("\nACCIONES ADICIONALES RECOMENDADAS:")
    print("1. Verifique los archivos modificados para asegurarse de que no hay errores.")
    print("2. Actualice las importaciones en app.py si es necesario.")
    print("3. Pruebe la aplicación para confirmar que funciona correctamente.")
    print("4. Si todo funciona, puede eliminar el directorio de datos si ya no es necesario.")

if __name__ == "__main__":
    main()
