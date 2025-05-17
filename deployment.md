---
name: energia_app
description: Sistema Predictivo de Consumo Energético para la Universidad de Cundinamarca
framework: Flask
runtime: Python 3.11.0
created: 2025
authors:
  - Oscar Giovanni Robayo Olaya
  - Diego Armando Guzmán Garzón
---

# Despliegue y ejecución

Esta guía proporciona instrucciones detalladas para desplegar y ejecutar la aplicación `energia_app` tanto en un entorno de desarrollo local como en producción.

## Entorno de desarrollo local

### Requisitos previos

- Python 3.11.0
- Pip (gestor de paquetes de Python)
- Git (opcional, para clonar el repositorio)

### Pasos para la ejecución local

1. **Clonar el repositorio** (si no lo has hecho ya):
   ```bash
   git clone <url-del-repositorio>
   cd energia_app
   ```

2. **Crear un entorno virtual**:
   ```bash
   # Crear entorno virtual
   python -m venv venv
   
   # Activar el entorno virtual
   # En Windows:
   venv\Scripts\activate
   # En macOS/Linux:
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**:
   ```bash
   python app.py
   ```

5. **Acceder a la aplicación**:
   Abre un navegador web y navega a `http://127.0.0.1:5000/`

## Despliegue en producción

### Opción 1: Despliegue con Gunicorn

1. **Instalar Gunicorn** (incluido en requirements.txt):
   ```bash
   pip install gunicorn
   ```

2. **Ejecutar con Gunicorn**:
   ```bash
   gunicorn app:app -w 4 -b 0.0.0.0:8000
   ```
   Donde:
   - `-w 4`: Número de workers (ajustar según CPU disponibles)
   - `-b 0.0.0.0:8000`: Dirección y puerto de bind

3. **Configurar un servidor proxy inverso** (Nginx recomendado):
   
   Ejemplo de configuración para Nginx:
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Opción 2: Despliegue en entornos cloud (PaaS)

#### Despliegue en Heroku

1. **Crear un archivo `Procfile`** (ya incluido):
   ```
   web: gunicorn app:app
   ```

2. **Login a Heroku y despliegue**:
   ```bash
   # Instalar CLI de Heroku (si no está instalado)
   # Seguir instrucciones en: https://devcenter.heroku.com/articles/heroku-cli
   
   # Login a Heroku
   heroku login
   
   # Crear aplicación en Heroku
   heroku create energia-app
   
   # Desplegar a Heroku
   git push heroku main
   ```

3. **Abrir la aplicación**:
   ```bash
   heroku open
   ```

#### Despliegue en Google Cloud Run

1. **Crear un archivo `Dockerfile`**:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   # Gunicorn para servir la aplicación
   CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
   ```

2. **Construir y desplegar usando Google Cloud Build**:
   ```bash
   # Configurar gcloud CLI (si no está configurado)
   gcloud init
   
   # Construir y desplegar
   gcloud builds submit --tag gcr.io/[PROJECT-ID]/energia-app
   gcloud run deploy energia-app --image gcr.io/[PROJECT-ID]/energia-app --platform managed
   ```

## Variables de entorno

Para configurar la aplicación en diferentes entornos, puedes utilizar las siguientes variables de entorno:

- `FLASK_ENV`: Entorno de Flask (`development`, `production`)
- `FLASK_DEBUG`: Modo debug (`0`, `1`)
- `DATABASE_URL`: URL de conexión a la base de datos (si se implementa)
- `SECRET_KEY`: Clave secreta para sesiones y tokens

Ejemplo de configuración con variables de entorno:
```bash
# En desarrollo
export FLASK_ENV=development
export FLASK_DEBUG=1
export SECRET_KEY="tu-clave-secreta-aqui"

# En producción
export FLASK_ENV=production
export FLASK_DEBUG=0
export SECRET_KEY="tu-clave-secreta-aqui"

Para el correcto funcionamiento del sistema de autenticación en producción, configure las siguientes variables de entorno:

```bash
# Requeridas para la autenticación y base de datos
export SECRET_KEY="clave-secreta-muy-segura-para-produccion"
export DATABASE_URL="postgresql://usuario:password@hostname/database"
```

### Notas importantes:
- La `SECRET_KEY` debe ser una cadena aleatoria y segura, usada para firmar las cookies de sesión
- Para PostgreSQL en Heroku, la variable `DATABASE_URL` se configura automáticamente
- Para otros proveedores como Render o Google Cloud Run, configure manualmente estas variables en su panel de control
```

Ejemplo de configuración en Render:
1. En el dashboard de Render, seleccione su servicio
2. Vaya a la pestaña "Environment"
3. Añada las variables `SECRET_KEY` y `DATABASE_URL` con sus valores correspondientes
```

## Supervisión y logs

### Logs de la aplicación

- **En desarrollo**: Los logs se muestran en la consola
- **En producción con Gunicorn**: Los logs se envían a stdout/stderr
- **En Heroku**: `heroku logs --tail`

### Monitorización

Se recomienda implementar una solución de monitorización como:
- New Relic
- Datadog
- Prometheus + Grafana

## Resolución de problemas comunes

1. **Error al cargar el modelo**:
   - Verifica que el directorio `energia_app/models` sea escribible
   - El modelo se generará automáticamente al primer acceso

2. **Error en la visualización de gráficas**:
   - Asegúrate de tener una conexión a internet para cargar Chart.js
   - Verifica la consola del navegador para errores JavaScript

3. **Problemas de rendimiento**:
   - Ajusta el número de workers de Gunicorn según los recursos disponibles
   - Considera implementar caché para las consultas frecuentes

## Notas de seguridad

1. No exponer directamente la aplicación en producción sin un proxy inverso
2. Cambiar la clave secreta (`SECRET_KEY`) en producción
3. Mantener actualizadas las dependencias con `pip-audit`

# Guía de implementación: Módulo de carga de dataset CSV

## Archivos creados o modificados

1. **Nuevo módulo para carga de datasets**:
   - `energia_app/utils/data_loader.py`: Contiene funciones para cargar, validar y analizar datasets CSV.

2. **Modificaciones en el archivo principal**:
   - `app.py`: Se agregaron nuevas rutas y funcionalidades para gestionar datasets.

3. **Nuevas plantillas HTML**:
   - `energia_app/templates/dataset.html`: Interfaz para gestión de datasets.

4. **Actualizaciones en archivos existentes**:
   - `energia_app/utils/__init__.py`: Importa las nuevas funciones del módulo data_loader.
   - `energia_app/templates/admin.html`: Incluye enlaces a la gestión de datasets.

5. **Archivos de ejemplo**:
   - `energia_app/data/energy_data_template.csv`: Plantilla de ejemplo para que los usuarios puedan descargar.

## Nuevas funcionalidades

1. **Carga de datasets desde CSV**:
   - Permite a los administradores subir archivos CSV con datos de consumo energético.
   - Valida que el formato de los datos sea correcto y contiene las columnas necesarias.

2. **Visualización de estadísticas del dataset**:
   - Muestra métricas importantes como el número de registros, rangos de valores y correlaciones.

3. **Reentrenamiento del modelo**:
   - Permite reentrenar el modelo con los nuevos datos cargados.
   - Muestra las métricas de rendimiento del modelo después del reentrenamiento.

4. **Descarga de datos**:
   - Los usuarios pueden descargar los datos actuales o una plantilla de ejemplo.

## Estructura del dataset

El sistema espera que el archivo CSV tenga la siguiente estructura:

- `area_edificio`: Área del edificio en metros cuadrados (numérico).
- `ocupacion`: Número de personas en el edificio (entero).
- `dia_semana`: Día de la semana (0-6, donde 0 es lunes).
- `hora_dia`: Hora del día (0-23).
- `consumo_energetico`: Consumo de energía en kWh (numérico).

## Flujo de trabajo

1. El administrador accede a la página de gestión de datasets (`/dataset`).
2. Sube un archivo CSV con datos de consumo energético.
3. El sistema valida el formato y contenido del archivo.
4. Si la validación es exitosa, el archivo se guarda y se muestran estadísticas.
5. Opcionalmente, el modelo se reentrena con los nuevos datos.
6. Los nuevos datos se utilizan automáticamente para futuras predicciones y visualizaciones en el dashboard.

## Manejo de errores

- Si el archivo no tiene el formato correcto, se muestra un mensaje de error.
- Si hay valores inválidos en las columnas importantes, se informa al usuario.
- Si el reentrenamiento falla, se muestra un mensaje con el error específico.

## Requisitos técnicos

- Flask para gestionar la carga de archivos y rutas.
- Pandas para el análisis y manipulación de datos.
- Scikit-learn para el reentrenamiento del modelo.

## Cambios en la configuración

- `app.config['UPLOAD_FOLDER']`: Directorio donde se guardan los archivos CSV.
- `app.config['MAX_CONTENT_LENGTH']`: Límite de tamaño de archivo (16 MB).
- `app.config['ALLOWED_EXTENSIONS']`: Extensiones de archivo permitidas (solo CSV).

## Rutas del sistema

- `/dataset`: Página principal de gestión de datasets.
- `/download/<filename>`: Descarga de archivos CSV.
- `/retrain`: Reentrenamiento del modelo con los datos actuales.

## Mejoras futuras

- Implementar validación más avanzada de datos.
- Añadir soporte para otros formatos (Excel, JSON).
- Proporcionar visualizaciones preliminares de los datos antes de guardarlos.
- Implementar funcionalidad para limpiar y preprocesar los datos durante la carga.
- Añadir opciones de configuración para el reentrenamiento del modelo.
