# Proyecto de Predicción de Consumo Energético - UDEC

Este proyecto implementa un sistema de predicción de consumo energético basado en Machine Learning para la Universidad de Cundinamarca - Sede Chía, contribuyendo al ODS 7: "Energía asequible y no contaminante".

## Descripción

El sistema permite:
- Predecir el consumo energético de edificios basado en su área, ocupación, día de la semana y hora del día
- Visualizar patrones de consumo a través de un dashboard interactivo
- Generar recomendaciones personalizadas para optimizar el uso de la energía

## Estructura del proyecto

```
energia_app/
│
├── __pycache__/
├── data/
│   └── synthetic_energy_data.csv       # Datos sintéticos generados para entrenamiento
│
├── models/
│   ├── __init__.py                     # Inicializador del paquete models
│   ├── model.py                        # Modelo de regresión lineal
│   └── preprocess.py                   # Funciones de preprocesamiento de datos
│
├── static/
│   ├── css/
│   │   └── style.css                   # Estilos personalizados
│   ├── img/
│   │   ├── UdeC.jpg                    # Logo de la universidad
│   │   └── energy_graph.png            # Gráfico de ejemplo para la página de predicción
│   └── js/
│       └── charts.js                   # Script para generar gráficas en el dashboard
│
├── templates/
│   ├── dashboard.html                  # Plantilla para visualización de datos
│   ├── index.html                      # Página de inicio
│   └── prediction.html                 # Formulario de predicción y resultados
│
└── utils/
    ├── __init__.py                     # Inicializador del paquete utils
    └── data_generator.py               # Funciones para generar datos sintéticos
│
app.py                                  # Aplicación principal Flask
requirements.txt                        # Dependencias del proyecto
runtime.txt                             # Versión de Python
```

## Requisitos

- Python 3.11.0
- Flask 2.3.3
- NumPy 1.26.0+
- Pandas 2.1.0+
- scikit-learn 1.3.0+

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/energia_app.git
cd energia_app
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:
```bash
python app.py
```

5. Acceder a la aplicación en tu navegador:
```
http://127.0.0.1:5000/
```

## Descripción de Componentes Principales

### 1. Modelo de Predicción (`models/model.py`)

Implementa un modelo de regresión lineal para predecir el consumo energético basado en:
- Área del edificio
- Nivel de ocupación
- Día de la semana
- Hora del día

El modelo se entrena automáticamente con datos sintéticos la primera vez que se ejecuta la aplicación.

### 2. Preprocesamiento de Datos (`models/preprocess.py`)

Transformaciones aplicadas a los datos de entrada:
- Normalización de variables numéricas
- Transformación de variables cíclicas (día de la semana, hora del día) a representaciones sinusoidales
- Creación de características derivadas (es_dia_laboral, es_hora_laboral, etc.)

### 3. Generación de Datos Sintéticos (`utils/data_generator.py`)

Genera datos de entrenamiento sintéticos basados en patrones realistas de consumo energético:
- Variación por día de la semana (menor en fines de semana)
- Variación por hora (picos durante horas laborales)
- Relación con área del edificio y nivel de ocupación

### 4. Dashboard de Visualización (`templates/dashboard.html`)

Presenta visualizaciones interactivas:
- Consumo por hora del día
- Consumo por día de la semana
- Comparativa entre edificios
- Análisis de tendencias

## Correcciones realizadas

1. Se creó el archivo `app.py` principal que faltaba
2. Se corrigió el import en `data_generator.py` para usar imports relativos
3. Se actualizó el contenido pendiente en `dashboard.html`
4. Se mejoró el manejo de errores en varios componentes

## Próximos pasos / mejoras

1. Implementar autenticación de usuarios
2. Añadir más modelos de predicción para comparar rendimiento
3. Incorporar datos reales de sensores del campus
4. Desarrollar una API REST para integración con otros sistemas
5. Implementar notificaciones automáticas para alertas de consumo anormal

## Contribución al ODS 7

Este proyecto contribuye a la meta 7.3 del ODS 7: "De aquí a 2030, duplicar la tasa mundial de mejora de la eficiencia energética" mediante:

1. Monitoreo y predicción del consumo energético
2. Identificación de patrones de consumo ineficiente
3. Generación de recomendaciones específicas para reducir el consumo
4. Concientización sobre el uso eficiente de la energía

## Autores

- Oscar Giovanni Robayo Olaya
- Diego Armando Guzmán Garzón

## Licencia

Este proyecto está bajo la Licencia MIT.