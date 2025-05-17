Sistema Predictivo de Consumo Energético
Este sistema utiliza técnicas de Machine Learning para predecir y optimizar el consumo energético en edificios del campus de la Universidad de Cundinamarca - Sede Chía, contribuyendo al cumplimiento del ODS 7: "Energía asequible y no contaminante".

Características principales
Predicción de consumo: Estima el consumo energético basado en área del edificio, ocupación, día de la semana y hora del día.
Recomendaciones personalizadas: Proporciona sugerencias específicas para optimizar el uso de energía según los parámetros introducidos.
Dashboard interactivo: Visualiza patrones y tendencias de consumo energético mediante gráficas dinámicas.
Alineación con ODS 7: Contribuye directamente a la eficiencia energética y la sostenibilidad ambiental.
Tecnologías utilizadas
Backend: Flask (Python)
Frontend: HTML, CSS, JavaScript, Bootstrap 5
Visualización: Chart.js
Machine Learning: scikit-learn
Procesamiento de datos: NumPy, Pandas
Estructura del proyecto
energia_app/
├── data/                     # Datos de entrenamiento y prueba
├── models/                   # Modelos ML y archivos relacionados
│   ├── __init__.py
│   ├── model.py              # Clase principal del modelo
│   └── preprocess.py         # Funciones de preprocesamiento
├── static/                   # Activos estáticos
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── charts.js
│   └── img/
├── templates/                # Plantillas HTML
│   ├── dashboard.html
│   ├── index.html
│   └── prediction.html
├── utils/                    # Utilidades y funciones auxiliares
│   ├── __init__.py
│   └── data_generator.py     # Generador de datos sintéticos
├── app.py                    # Aplicación principal
└── requirements.txt          # Dependencias
Requisitos
Python 3.8 o superior
Dependencias listadas en requirements.txt
Instalación
Clonar el repositorio:
bash
git clone [URL_DEL_REPOSITORIO]
cd energia_app
Crear y activar un entorno virtual (opcional pero recomendado):
bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
Instalar dependencias:
bash
pip install -r requirements.txt
Iniciar la aplicación:
bash
python app.py
Acceder a la aplicación en el navegador:
http://localhost:5000
Uso
Página principal: Muestra información general sobre el proyecto y sus objetivos.
Predicción: Ingrese los parámetros (área, ocupación, día, hora) para obtener una estimación del consumo energético y recomendaciones personalizadas.
Dashboard: Visualiza patrones de consumo por hora, día de la semana y edificio, así como tendencias históricas y recomendaciones principales.
Modelo de Machine Learning
El sistema utiliza un modelo de regresión lineal para predecir el consumo energético. Características del modelo:

Características de entrada: Área del edificio, nivel de ocupación, día de la semana, hora del día.
Preprocesamiento: Transformación de variables cíclicas (día, hora) mediante codificación con seno y coseno, normalización de variables numéricas.
Técnicas aplicadas: División en entrenamiento/prueba, normalización de características, evaluación de importancia de características.
Métricas de evaluación: MSE, RMSE, R².
Autores
Oscar Giovanni Robayo Olaya
Diego Armando Guzmán Garzón
Licencia
Este proyecto es parte del curso de Machine Learning en la Universidad de Cundinamarca - 2025.

