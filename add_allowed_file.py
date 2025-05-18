import os
import re
from datetime import datetime

# Configuración
APP_PY_PATH = 'app.py'
BACKUP_PATH = f'app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'

def add_allowed_file_function():
    """Añade la función allowed_file al archivo app.py"""
    try:
        # Crear backup
        with open(APP_PY_PATH, 'r', encoding='utf-8') as src:
            with open(BACKUP_PATH, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"Backup creado en: {BACKUP_PATH}")
        
        # Leer contenido
        with open(APP_PY_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Verificar si la función ya existe
        if 'def allowed_file(' in content:
            print("La función allowed_file ya existe en app.py")
        else:
            # Encontrar un buen lugar para insertar la función
            # Buscamos después de las importaciones y antes de la primera ruta
            match = re.search(r'(# Rutas de autenticación|@app\.route)', content)
            if match:
                insert_pos = match.start()
                allowed_file_func = '''
def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

'''
                # Insertar la función
                new_content = content[:insert_pos] + allowed_file_func + content[insert_pos:]
                
                # Guardar cambios
                with open(APP_PY_PATH, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                print("Función allowed_file añadida correctamente")
            else:
                print("No se pudo encontrar un lugar adecuado para insertar la función. Añádela manualmente.")
                return False
        
        # Verificar si las configuraciones existen
        config_pattern = r"app\.config\['ALLOWED_EXTENSIONS'\]\s*="
        if not re.search(config_pattern, content):
            # Buscar el bloque de configuración
            config_block = re.search(r"app\.config\['SECRET_KEY'\]", content)
            if config_block:
                # Encontrar el final del bloque de configuración
                config_end = content.find('\n\n', config_block.start())
                if config_end == -1:  # Si no hay doble salto de línea
                    config_end = content.find('\n', config_block.start())
                
                # Preparar configuraciones
                app_config = '''
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
'''
                # Insertar configuraciones
                new_content = content[:config_end] + app_config + content[config_end:]
                
                # Guardar cambios
                with open(APP_PY_PATH, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                print("Configuraciones añadidas correctamente")
            else:
                print("No se pudo encontrar el bloque de configuración. Añade las configuraciones manualmente.")
                return False
        else:
            print("Las configuraciones ya existen en app.py")
        
        # Añadir código para crear el directorio si no existe
        if 'os.makedirs(app.config[\'UPLOAD_FOLDER\'], exist_ok=True)' not in content:
            # Buscar después del bloque de configuración
            folder_pattern = r"app\.config\['UPLOAD_FOLDER'\]"
            match = re.search(folder_pattern, content)
            if match:
                # Encontrar el final de la línea
                line_end = content.find('\n', match.start())
                
                # Preparar código para crear directorio
                mkdir_code = '''
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Crear el directorio si no existe
'''
                # Insertar código
                new_content = content[:line_end] + mkdir_code + content[line_end:]
                
                # Guardar cambios
                with open(APP_PY_PATH, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                print("Código para crear el directorio añadido correctamente")
            else:
                print("No se pudo encontrar la configuración UPLOAD_FOLDER. Añade el código manualmente.")
                return False
        else:
            print("El código para crear el directorio ya existe en app.py")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Añadiendo función allowed_file y configuraciones a app.py ===")
    success = add_allowed_file_function()
    
    if success:
        print("\n¡Proceso completado con éxito!")
        print("Ahora puedes ejecutar app.py sin errores de 'allowed_file'")
    else:
        print("\nEl proceso no se completó correctamente.")
        print("Por favor, añade la función y configuraciones manualmente.")
    
    print("\nFunción a añadir:")
    print("""
def allowed_file(filename):
    \"\"\"Verifica si la extensión del archivo es permitida\"\"\"
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
""")
    
    print("\nConfiguraciones a añadir:")
    print("""
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Crear el directorio si no existe
""")