#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para generar la estructura de carpetas del proyecto
'Sistema Predictivo de Consumo Energético' para la Universidad de Cundinamarca - Sede Chía.
"""

import os

def crear_directorio(ruta):
    """Crea un directorio si no existe."""
    if not os.path.exists(ruta):
        os.makedirs(ruta)
        print(f"Directorio creado: {ruta}")
    else:
        print(f"El directorio ya existe: {ruta}")

def crear_archivo_vacio(ruta):
    """Crea un archivo vacío."""
    with open(ruta, 'w', encoding='utf-8') as archivo:
        pass
    print(f"Archivo creado: {ruta}")

def main():
    # Directorio base del proyecto
    base_dir = "energia_app"
    
    # Crear directorio principal
    crear_directorio(base_dir)
    
    # Estructura de carpetas
    directorios = [
        os.path.join(base_dir, "models"),
        os.path.join(base_dir, "templates"),
        os.path.join(base_dir, "static"),
        os.path.join(base_dir, "static", "css"),
        os.path.join(base_dir, "static", "js"),
        os.path.join(base_dir, "static", "img"),
        os.path.join(base_dir, "utils"),
        os.path.join(base_dir, "data")
    ]
    
    # Crear todos los directorios
    for directorio in directorios:
        crear_directorio(directorio)
    
    # Archivos principales
    archivos = [
        os.path.join(base_dir, "app.py"),
        os.path.join(base_dir, "requirements.txt"),
        os.path.join(base_dir, "README.md"),
        os.path.join(base_dir, "models", "__init__.py"),
        os.path.join(base_dir, "models", "model.py"),
        os.path.join(base_dir, "models", "preprocess.py"),
        os.path.join(base_dir, "utils", "__init__.py"),
        os.path.join(base_dir, "utils", "data_generator.py"),
        os.path.join(base_dir, "static", "css", "style.css"),
        os.path.join(base_dir, "static", "js", "charts.js"),
        os.path.join(base_dir, "templates", "index.html"),
        os.path.join(base_dir, "templates", "prediction.html"),
        os.path.join(base_dir, "templates", "dashboard.html")
    ]
    
    # Crear todos los archivos vacíos
    for archivo in archivos:
        crear_archivo_vacio(archivo)
    
    print("\n¡Estructura del proyecto creada exitosamente!")
    print(f"\nSe ha generado la siguiente estructura en la carpeta '{base_dir}':")
    print("""
/energia_app/
├── app.py                # Aplicación principal Flask
├── models/               # Módulo para modelos ML
│   ├── __init__.py
│   ├── model.py          # Modelo de regresión lineal
│   └── preprocess.py     # Preprocesamiento de datos
├── static/               # Archivos estáticos
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── charts.js
│   └── img/              # Carpeta para imágenes
├── templates/            # Plantillas HTML
│   ├── index.html
│   ├── prediction.html
│   └── dashboard.html
├── utils/                # Utilidades
│   ├── __init__.py
│   └── data_generator.py # Generador de datos sintéticos
├── data/                 # Carpeta para datos
└── requirements.txt      # Dependencias
""")

if __name__ == "__main__":
    main()
