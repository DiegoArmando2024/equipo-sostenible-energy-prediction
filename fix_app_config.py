# fix_app_config.py
"""
Script para corregir las configuraciones de app.py y asegurarse
de que UPLOAD_FOLDER se define antes de utilizarlo.
"""

import os
import re
from datetime import datetime
import shutil

# Configuración
APP_PY_PATH = 'app.py'
BACKUP_PATH = f'app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'

def fix_app_config():
    """Corrige la configuración de app.py"""
    # Verificar si el archivo existe
    if not os.path.exists(APP_PY_PATH):
        print(f"¡Error! No se encontró el archivo {APP_PY_PATH}")
        return False
    
    # Crear backup
    shutil.copy2(APP_PY_PATH, BACKUP_PATH)
    print(f"Backup creado en: {BACKUP_PATH}")
    
    # Leer el contenido
    with open(APP_PY_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Buscar el bloque de configuración
    app_config_pattern = r"app = Flask\(.*?\)\s*\n\n# Configuración de la aplicación\napp\.config\['SECRET_KEY'\]"
    match = re.search(app_config_pattern, content, re.DOTALL)
    
    if match:
        # Encontrar el final del bloque de configuración
        config_start = match.end()
        next_section = re.search(r"\n\n# ", content[config_start:])
        if next_section:
            config_end = config_start + next_section.start()
        else:
            config_end = len(content)
        
        # Extraer el bloque de configuración actual
        config_block = content[config_start:config_end]
        
        # Verificar qué configuraciones ya existen
        has_allowed_ext = 'ALLOWED_EXTENSIONS' in config_block
        has_upload_folder = 'UPLOAD_FOLDER' in config_block
        has_max_content = 'MAX_CONTENT_LENGTH' in config_block
        
        # Preparar nuevas configuraciones
        new_config = "app.config['SECRET_KEY']" + config_block
        if not has_upload_folder:
            new_config += "\napp.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')"
        if not has_max_content:
            new_config += "\napp.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max-limit"
        if not has_allowed_ext:
            new_config += "\napp.config['ALLOWED_EXTENSIONS'] = {'csv'}"
        
        # Crear código para los directorios
        dir_code = "\n\n# Crear directorios necesarios\nos.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Crear directorio de datos"
        
        # Reemplazar el bloque de configuración
        new_content = content[:config_start - len("app.config['SECRET_KEY']")] + new_config + dir_code + content[config_end:]
        
        # Guardar el archivo
        with open(APP_PY_PATH, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print("Configuraciones actualizadas con éxito")
        return True
    else:
        # Si no encontramos el patrón exacto, busquemos un punto de inserción alternativo
        # Después de la creación de la app
        app_creation = re.search(r"app = Flask\(.*?\)", content, re.DOTALL)
        if app_creation:
            insert_pos = app_creation.end()
            
            # Preparar bloque de configuración completo
            config_block = """

# Configuración de la aplicación
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-predeterminada')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///energia_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max-limit
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Crear directorio de datos
"""
            # Insertar el bloque
            new_content = content[:insert_pos] + config_block + content[insert_pos:]
            
            # Guardar el archivo
            with open(APP_PY_PATH, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            print("Se ha añadido un nuevo bloque de configuración completo")
            return True
        else:
            print("No se pudo encontrar un punto adecuado para insertar las configuraciones")
            return False

def main():
    """Función principal"""
    print("=== Corrigiendo configuraciones de app.py ===")
    success = fix_app_config()
    
    if success:
        print("\n¡Proceso completado con éxito!")
        print("Ahora puedes ejecutar app.py sin errores de configuración")
    else:
        print("\nEl proceso no se completó correctamente.")
        print("Por favor, añade las configuraciones manualmente.")
    
    print("\nConfiguraciones necesarias:")
    print("""
# Configuración de la aplicación
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-predeterminada')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///energia_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max-limit
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Crear directorio de datos
""")

if __name__ == "__main__":
    main()