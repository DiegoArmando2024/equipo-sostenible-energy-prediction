#!/usr/bin/env python3
"""
Script para reorganizar la estructura del proyecto de Sistema Predictivo de Consumo Energético.
Crea una estructura de directorios estándar, identifica y mueve archivos existentes a sus ubicaciones correctas,
y crea los archivos faltantes esenciales.
"""

import os
import shutil
import logging
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('reorganize_structure.log', mode='w')
    ]
)
logger = logging.getLogger('reorganize_structure')

# Estructura de directorios deseada
DIRECTORY_STRUCTURE = [
    'energia_app/',
    'energia_app/data/',
    'energia_app/models/',
    'energia_app/static/',
    'energia_app/static/css/',
    'energia_app/static/js/',
    'energia_app/static/img/',
    'energia_app/templates/',
    'energia_app/utils/',
]

# Archivos que deben estar presentes en cada directorio
REQUIRED_FILES = {
    'energia_app/models/': ['__init__.py', 'model.py', 'preprocess.py'],
    'energia_app/static/css/': ['style.css'],
    'energia_app/static/js/': ['charts.js'],
    'energia_app/static/img/': [],  # Será generado por otro script
    'energia_app/templates/': ['dashboard.html', 'index.html', 'prediction.html', 'error.html'],
    'energia_app/utils/': ['__init__.py', 'data_generator.py'],
    'energia_app/': ['app.py', 'Procfile', 'requirements.txt', 'README.md', '.gitignore'],
}

# Definición del contenido para los archivos faltantes
GITIGNORE_CONTENT = """__pycache__/
*.py[cod]
*$py.class
venv/
env/
.env
*.pkl
.vscode/
.idea/
*.log
"""

ERROR_HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - UDEC Sistema Predictivo de Consumo Energético</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <!-- Estilos personalizados -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <img src="{{ url_for('static', filename='img/UdeC.jpg') }}" height="40" alt="UDEC">
                Sistema Predictivo de Consumo Energético
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Inicio</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/predict">Predicción</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard">Dashboard</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow-sm">
                    <div class="card-header bg-danger text-white">
                        <h3 class="mb-0">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            {{ error_title|default('Ha ocurrido un error') }}
                        </h3>
                    </div>
                    <div class="card-body p-4">
                        <div class="text-center mb-4">
                            <i class="bi bi-x-circle text-danger" style="font-size: 4rem;"></i>
                        </div>
                        
                        <p class="lead text-center">
                            {{ error_message|default('Lo sentimos, se ha producido un error al procesar su solicitud.') }}
                        </p>
                        
                        {% if error_details %}
                        <div class="alert alert-secondary mt-3">
                            <h5>Detalles técnicos:</h5>
                            <code>{{ error_details }}</code>
                        </div>
                        {% endif %}
                        
                        <div class="d-grid gap-2 d-md-flex justify-content-center mt-4">
                            <a href="{{ back_url|default('/') }}" class="btn btn-outline-secondary">
                                <i class="bi bi-arrow-left me-1"></i> Volver
                            </a>
                            <a href="/" class="btn btn-primary">
                                <i class="bi bi-house-door me-1"></i> Ir a inicio
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5>Sistema Predictivo de Consumo Energético</h5>
                    <p>Universidad de Cundinamarca - Sede Chía</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <p>
                        Desarrollado por: Oscar Giovanni Robayo Olaya y Diego Armando Guzmán Garzón <br>
                        Curso de Machine Learning - 2025
                    </p>
                </div>
            </div>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

def create_directory_structure():
    """Crea la estructura de directorios si no existe."""
    for directory in DIRECTORY_STRUCTURE:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.info(f"Directorio creado: {directory}")
            except Exception as e:
                logger.error(f"Error al crear directorio {directory}: {str(e)}")
                raise

def find_files(directory='.'):
    """
    Encuentra todos los archivos en el directorio actual y subdirectorios.
    
    Args:
        directory (str): Directorio a buscar.
        
    Returns:
        dict: Diccionario con la ruta de archivo como clave y la ruta completa como valor.
    """
    files = {}
    try:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                # Excluir archivos .log, .git, y otros archivos no necesarios
                if (filename.endswith('.log') or '.git' in root or
                    '__pycache__' in root or filename.endswith('.pyc')):
                    continue
                
                filepath = os.path.join(root, filename)
                files[filename] = filepath
        
        logger.info(f"Se encontraron {len(files)} archivos en el directorio {directory}")
        return files
    except Exception as e:
        logger.error(f"Error al buscar archivos en {directory}: {str(e)}")
        raise

def identify_and_move_files():
    """
    Identifica los archivos existentes y los mueve a las ubicaciones correctas.
    """
    all_files = find_files()
    moved_files = []
    
    # Mapeo de archivos a sus destinos correspondientes
    file_destinations = {
        'app.py': 'energia_app/app.py',
        'Procfile': 'energia_app/Procfile',
        'README.md': 'energia_app/README.md',
        'requirements.txt': 'energia_app/requirements.txt',
        '.gitignore': 'energia_app/.gitignore',
        'model.py': 'energia_app/models/model.py',
        'preprocess.py': 'energia_app/models/preprocess.py',
        'style.css': 'energia_app/static/css/style.css',
        'charts.js': 'energia_app/static/js/charts.js',
        'dashboard.html': 'energia_app/templates/dashboard.html',
        'index.html': 'energia_app/templates/index.html',
        'prediction.html': 'energia_app/templates/prediction.html',
        'data_generator.py': 'energia_app/utils/data_generator.py',
    }
    
    # Intentar mover cada archivo encontrado a su destino correcto
    for filename, filepath in all_files.items():
        if filename in file_destinations:
            destination = file_destinations[filename]
            destination_dir = os.path.dirname(destination)
            
            # Asegurar que el directorio de destino existe
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            
            try:
                # Si el archivo ya está en la ubicación correcta o hay duplicados, 
                # elegir la versión más reciente
                if os.path.exists(destination) and os.path.getmtime(filepath) <= os.path.getmtime(destination):
                    logger.info(f"Saltando {filename}, ya existe una versión más reciente en {destination}")
                    continue
                
                # Verificar si el archivo está en energia_app/ o en la raíz
                # Si está en energia_app/ y la ruta de destino también es en energia_app/, usar la versión de energia_app/
                if 'energia_app/' in filepath:
                    source_path = Path(filepath)
                    dest_path = Path(destination)
                    if str(source_path.relative_to(Path.cwd())) == str(dest_path):
                        logger.info(f"Archivo ya en posición correcta: {filepath}")
                        continue
                
                # Copiar el archivo a su destino
                shutil.copy2(filepath, destination)
                logger.info(f"Archivo copiado: {filepath} -> {destination}")
                moved_files.append((filename, destination))
            except Exception as e:
                logger.error(f"Error al mover archivo {filename}: {str(e)}")
    
    return moved_files

def create_missing_files():
    """
    Crea los archivos faltantes pero esenciales.
    """
    created_files = []
    
    # Verificar todos los archivos requeridos
    for directory, files in REQUIRED_FILES.items():
        for filename in files:
            filepath = os.path.join(directory, filename)
            
            # Si el archivo no existe, crearlo con contenido predeterminado
            if not os.path.exists(filepath):
                try:
                    # Determinar el contenido según el archivo
                    content = ""
                    if filename == '__init__.py':
                        if 'models' in directory:
                            content = """
from .model import Energy_Model
from .preprocess import preprocess_data

__all__ = ['Energy_Model', 'preprocess_data']"""
                        elif 'utils' in directory:
                            content = """
from .data_generator import generate_synthetic_data, generate_future_scenarios
__all__ = ['generate_synthetic_data', 'generate_future_scenarios']"""
                    elif filename == '.gitignore':
                        content = GITIGNORE_CONTENT
                    elif filename == 'error.html':
                        content = ERROR_HTML_CONTENT
                    
                    # Escribir contenido al archivo
                    with open(filepath, 'w') as f:
                        f.write(content)
                    
                    logger.info(f"Archivo creado: {filepath}")
                    created_files.append(filepath)
                except Exception as e:
                    logger.error(f"Error al crear archivo {filepath}: {str(e)}")
    
    return created_files

def remove_redundant_files(moved_files):
    """
    Elimina archivos redundantes (los que han sido movidos a energia_app/).
    
    Args:
        moved_files (list): Lista de tuplas (nombre_archivo, ruta_destino)
    """
    deleted_files = []
    
    for filename, destination in moved_files:
        # Solo eliminar archivos fuera de energia_app/
        if not destination.startswith('energia_app/'):
            continue
        
        original_files = []
        for root, _, filenames in os.walk('.'):
            # Ignorar archivos dentro de energia_app/
            if 'energia_app' in root:
                continue
            
            # Buscar archivos con el mismo nombre fuera de energia_app/
            for fname in filenames:
                if fname == filename:
                    original_path = os.path.join(root, fname)
                    original_files.append(original_path)
        
        # Eliminar los archivos originales (ahora redundantes)
        for original_path in original_files:
            try:
                os.remove(original_path)
                logger.info(f"Archivo eliminado: {original_path}")
                deleted_files.append(original_path)
            except Exception as e:
                logger.error(f"Error al eliminar archivo {original_path}: {str(e)}")
    
    return deleted_files

def main():
    """
    Función principal que ejecuta todas las tareas de reorganización.
    """
    logger.info("Iniciando reorganización de la estructura del proyecto")
    
    try:
        # Crear estructura de directorios
        logger.info("Creando estructura de directorios...")
        create_directory_structure()
        
        # Identificar y mover archivos existentes
        logger.info("Identificando y moviendo archivos existentes...")
        moved_files = identify_and_move_files()
        
        # Crear archivos faltantes
        logger.info("Creando archivos faltantes...")
        created_files = create_missing_files()
        
        # Eliminar archivos redundantes
        logger.info("Eliminando archivos redundantes...")
        deleted_files = remove_redundant_files(moved_files)
        
        # Resumen de operaciones
        logger.info(f"Reorganización completada:")
        logger.info(f"  - Directorios creados: {len(DIRECTORY_STRUCTURE)}")
        logger.info(f"  - Archivos movidos: {len(moved_files)}")
        logger.info(f"  - Archivos creados: {len(created_files)}")
        logger.info(f"  - Archivos eliminados: {len(deleted_files)}")
        
        return True
    except Exception as e:
        logger.error(f"Error durante la reorganización: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

