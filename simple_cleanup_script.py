#!/usr/bin/env python3
"""
Script simplificado para eliminar rutas y configuraciones redundantes en app.py
tras la simplificación del sistema de datos.

Este script es más directo y solo se enfoca en app.py, permitiendo
un control más manual sobre el proceso de limpieza.

Uso:
1. Hacer una copia de seguridad de app.py
2. Ejecutar: python simple_cleanup.py
"""

import os
import re
from datetime import datetime

# Archivo a modificar
APP_PY_PATH = 'app.py'
BACKUP_PATH = f'app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'

# Lista de bloques de código a eliminar (se buscarán por coincidencia exacta)
CODE_BLOCKS_TO_REMOVE = [
    # Ruta dataset_management
    """@app.route('/dataset-management')
@login_required
def dataset_management():
    \"\"\"Redirección a la página de gestión de datos (pestaña dataset)\"\"\"
    return redirect(url_for('data_management') + '#dataset')""",

    # Ruta export_to_dataset
    """@app.route('/export-to-dataset')
@login_required
def export_to_dataset():
    \"\"\"Exporta los datos de la base de datos a un dataset para entrenar el modelo\"\"\"
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('index'))
    
    try:
        # Exportar todos los datos a DataFrame
        data = EnergyData.export_to_df()
        
        # Guardar como CSV
        data_path = os.path.join(app.config['UPLOAD_FOLDER'], 'energy_data.csv')
        
        # Asegurar que el directorio existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Guardar datos
        data.to_csv(data_path, index=False)
        
        flash(f'Dataset exportado correctamente con {len(data)} registros.')
        return redirect(url_for('data_management'))
    except Exception as e:
        flash(f'Error al exportar dataset: {str(e)}')
        return redirect(url_for('data_management'))""",

    # Configuración del directorio de carga
    """app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max-limit
app.config['ALLOWED_EXTENSIONS'] = {'csv'}""",

    # Función allowed_file
    """def allowed_file(filename):
    \"\"\"Verifica si la extensión del archivo es permitida\"\"\"
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']"""
]

def create_backup():
    """Crea una copia de seguridad del archivo app.py"""
    shutil.copy2(APP_PY_PATH, BACKUP_PATH)
    print(f"Backup creado en: {BACKUP_PATH}")

def remove_code_blocks():
    """Elimina los bloques de código redundantes"""
    # Verificar existencia del archivo
    if not os.path.exists(APP_PY_PATH):
        print(f"¡Error! No se encontró el archivo {APP_PY_PATH}")
        return False
    
    # Leer contenido
    with open(APP_PY_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Hacer copia de seguridad del contenido original
    original_content = content
    
    # Contador de bloques eliminados
    removed_count = 0
    
    # Eliminar cada bloque
    for block in CODE_BLOCKS_TO_REMOVE:
        # Normalizar finales de línea
        normalized_block = block.replace('\r\n', '\n')
        normalized_content = content.replace('\r\n', '\n')
        
        # Verificar si el bloque existe
        if normalized_block in normalized_content:
            # Eliminar el bloque
            content = content.replace(block, '')
            removed_count += 1
        else:
            print(f"ADVERTENCIA: No se encontró el bloque exacto:\n{block[:50]}...")
    
    # Si no hubo cambios, terminar
    if content == original_content:
        print("No se realizaron cambios. Verifique si los bloques de código existen exactamente como se definen.")
        return False
    
    # Escribir archivo actualizado
    with open(APP_PY_PATH, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Se eliminaron {removed_count} bloques de código redundantes de {APP_PY_PATH}")
    return True

if __name__ == "__main__":
    import shutil
    
    print("=== Script de limpieza simple de código redundante ===")
    
    # Crear backup
    create_backup()
    
    # Eliminar código redundante
    if remove_code_blocks():
        print("\n¡Proceso completado con éxito!")
    else:
        print("\nEl proceso no realizó cambios.")
    
    print("\nACCIONES RECOMENDADAS:")
    print("1. Verifique app.py para asegurarse de que los cambios son correctos")
    print("2. Actualice las importaciones si es necesario")
    print("3. Pruebe la aplicación para confirmar que funciona correctamente")
