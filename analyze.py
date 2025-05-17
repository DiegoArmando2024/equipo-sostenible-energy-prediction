"""
Script para analizar datos de consumo energético y validar el modelo predictivo.
Este script puede usarse para:
1. Explorar patrones en los datos sintéticos
2. Validar el rendimiento del modelo
3. Generar visualizaciones adicionales
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split, cross_val_score

# Configuración para visualizaciones más atractivas
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")

def cargar_datos(ruta_archivo=None):
    """
    Carga los datos de consumo energético desde un archivo CSV.
    Si no se proporciona un archivo, busca en la ubicación por defecto.
    """
    if ruta_archivo is None:
        # Obtener directorio actual (donde se ejecuta el script)
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        
        # Construir ruta al archivo de datos
        ruta_archivo = os.path.join(dir_actual, 'energia_app', 'data', 'synthetic_energy_data.csv')
    
    # Verificar si el archivo existe
    if not os.path.exists(ruta_archivo):
        print(f"Error: No se encontró el archivo de datos en {ruta_archivo}")
        print("Si no has ejecutado la aplicación web, primero ejecútala para generar los datos sintéticos.")
        return None
    
    # Cargar datos
    try:
        datos = pd.read_csv(ruta_archivo)
        print(f"Datos cargados exitosamente: {len(datos)} registros")
        return datos
    except Exception as e:
        print(f"Error al cargar los datos: {str(e)}")
        return None

def analizar_datos(datos):
    """
    Realiza un análisis exploratorio de los datos de consumo energético.
    """
    if datos is None or len(datos) == 0:
        print("No hay datos para analizar.")
        return
    
    print("\n=== ANÁLISIS EXPLORATORIO DE DATOS ===\n")
    
    # Información general
    print(f"Dimensiones: {datos.shape}")
    print("\nPrimeras 5 filas:")
    print(datos.head())
    
    # Estadísticas descriptivas
    print("\nEstadísticas descriptivas:")
    print(datos.describe())
    
    # Verificar valores nulos
    nulos = datos.isnull().sum()
    if nulos.sum() > 0:
        print("\nValores nulos por columna:")
        print(nulos[nulos > 0])
    else:
        print("\nNo hay valores nulos en el conjunto de datos.")
    
    # Análisis por día de la semana
    print("\nConsumo promedio por día de la semana:")
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    consumo_dia = datos.groupby('dia_semana')['consumo_energetico'].mean().reset_index()
    consumo_dia['dia'] = consumo_dia['dia_semana'].apply(lambda x: dias[x])
    print(consumo_dia[['dia', 'consumo_energetico']])
    
    # Análisis por hora del día
    print("\nConsumo promedio por hora del día:")
    consumo_hora = datos.groupby('hora_dia')['consumo_energetico'].mean().reset_index()
    print(consumo_hora.head(10))  # Mostrar primeras 10 horas
    
    # Correlaciones
    print("\nMatriz de correlación:")
    corr = datos[['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']].corr()
    print(corr['consumo_energetico'].sort_values(ascending=False))

def visualizar_datos(datos):
    """
    Genera visualizaciones para explorar patrones en los datos.
    """
    if datos is None or len(datos) == 0:
        print("No hay datos para visualizar.")
        return
    
    print("\n=== VISUALIZACIONES DE DATOS ===\n")
    
    # Configurar figura principal
    plt.figure(figsize=(15, 12))
    
    # 1. Consumo por día de la semana
    plt.subplot(2, 2, 1)
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    consumo_dia = datos.groupby('dia_semana')['consumo_energetico'].mean().reset_index()
    
    sns.barplot(x='dia_semana', y='consumo_energetico', data=consumo_dia)
    plt.title('Consumo Energético Promedio por Día de la Semana')
    plt.xlabel('Día')
    plt.ylabel('Consumo (kWh)')
    plt.xticks(range(7), dias)
    
    # 2. Consumo por hora del día
    plt.subplot(2, 2, 2)
    consumo_hora = datos.groupby('hora_dia')['consumo_energetico'].mean().reset_index()
    
    sns.lineplot(x='hora_dia', y='consumo_energetico', data=consumo_hora, marker='o')
    plt.title('Consumo Energético Promedio por Hora del Día')
    plt.xlabel('Hora')
    plt.ylabel('Consumo (kWh)')
    plt.xticks(range(0, 24, 2))
    plt.grid(True)
    
    # 3. Relación entre área y consumo
    plt.subplot(2, 2, 3)
    sns.scatterplot(x='area_edificio', y='consumo_energetico', data=datos, alpha=0.5)
    plt.title('Relación entre Área del Edificio y Consumo Energético')
    plt.xlabel('Área (m²)')
    plt.ylabel('Consumo (kWh)')
    
    # 4. Relación entre ocupación y consumo
    plt.subplot(2, 2, 4)
    sns.scatterplot(x='ocupacion', y='consumo_energetico', data=datos, alpha=0.5)
    plt.title('Relación entre Ocupación y Consumo Energético')
    plt.xlabel('Ocupación (personas)')
    plt.ylabel('Consumo (kWh)')
    
    plt.tight_layout()
    
    # Guardar visualización
    try:
        plt.savefig('analisis_energia.png')
        print("Visualización guardada como 'analisis_energia.png'")
    except Exception as e:
        print(f"Error al guardar la visualización: {str(e)}")
    
    # Mostrar visualización
    plt.show()

def evaluar_modelo(datos):
    """
    Evalúa el rendimiento del modelo de regresión lineal
    """
    if datos is None or len(datos) == 0:
        print("No hay datos para evaluar el modelo.")
        return
    
    print("\n=== EVALUACIÓN DEL MODELO ===\n")
    
    # 1. Importar módulos necesarios
    try:
        from energia_app.models.preprocess import preprocess_data
        from energia_app.models.model import Energy_Model
    except ImportError as e:
        print(f"Error al importar módulos: {str(e)}")
        print("Asegúrate de ejecutar este script desde el directorio raíz del proyecto.")
        return
    
    # 2. Preprocesar datos
    try:
        X, y = preprocess_data(datos, training=True)
        print(f"Datos preprocesados: {X.shape[0]} muestras, {X.shape[1]} características")
    except Exception as e:
        print(f"Error en el preprocesamiento: {str(e)}")
        return
    
    # 3. Dividir datos en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Entrenar modelo
    model = Energy_Model()
    try:
        metrics = model.train(X_train, y_train)
        print("Modelo entrenado con éxito")
        print(f"Coeficientes: {metrics['coefficients']}")
        print(f"Intercepto: {metrics['intercept']}")
    except Exception as e:
        print(f"Error al entrenar el modelo: {str(e)}")
        return
    
    # 5. Evaluar modelo con datos de prueba
    y_pred = model.predict(X_test)
    
    # 6. Calcular métricas
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print("\nResultados de evaluación en conjunto de prueba:")
    print(f"Error cuadrático medio (MSE): {mse:.4f}")
    print(f"Raíz del error cuadrático medio (RMSE): {rmse:.4f}")
    print(f"Error absoluto medio (MAE): {mae:.4f}")
    print(f"Coeficiente de determinación (R²): {r2:.4f}")
    
    # 7. Visualizar predicciones vs valores reales
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    plt.title('Valores reales vs Predicciones')
    plt.xlabel('Consumo Real (kWh)')
    plt.ylabel('Consumo Predicho (kWh)')
    plt.grid(True)
    
    # Guardar visualización
    try:
        plt.savefig('evaluacion_modelo.png')
        print("Evaluación guardada como 'evaluacion_modelo.png'")
    except Exception as e:
        print(f"Error al guardar la evaluación: {str(e)}")
    
    plt.show()

def main():
    """
    Función principal que ejecuta el análisis completo.
    """
    print("=== ANÁLISIS DE DATOS DE CONSUMO ENERGÉTICO ===")
    
    # Cargar datos
    datos = cargar_datos()
    if datos is None:
        return
    
    # Menú de opciones
    while True:
        print("\nOpciones:")
        print("1. Analizar datos (estadísticas descriptivas)")
        print("2. Visualizar datos (gráficos)")
        print("3. Evaluar modelo de predicción")
        print("4. Ejecutar análisis completo")
        print("0. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1':
            analizar_datos(datos)
        elif opcion == '2':
            visualizar_datos(datos)
        elif opcion == '3':
            evaluar_modelo(datos)
        elif opcion == '4':
            analizar_datos(datos)
            visualizar_datos(datos)
            evaluar_modelo(datos)
        elif opcion == '0':
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida. Intente nuevamente.")

if __name__ == "__main__":
    main()
