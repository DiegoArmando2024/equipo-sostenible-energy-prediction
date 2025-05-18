/**
 * consolidated_charts.js
 * 
 * Archivo JavaScript centralizado para todas las gráficas del sistema.
 * Integra la funcionalidad existente en charts.js en un nuevo modelo organizado por secciones.
 * Implementado con manejo de errores mejorado y estructura modular.
 */

// Evento principal al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
    // Determinar en qué página nos encontramos para inicializar las gráficas correspondientes
    const currentPath = window.location.pathname;
    
    if (currentPath === '/dashboard') {
        initDashboardCharts();
    } else if (currentPath === '/buildings/dashboard' || currentPath.includes('/building_dashboard')) {
        initBuildingDashboardCharts();
    } else if (currentPath === '/predict' && document.getElementById('predictionResultCharts')) {
        initPredictionCharts();
    }
});

// ==================================================
// INICIALIZADORES DE GRÁFICAS PARA CADA PÁGINA
// ==================================================

/**
 * Inicializa las gráficas para el dashboard principal
 */
function initDashboardCharts() {
    // Intentar cargar datos de la API
    fetch('/api/data')
        .then(handleResponse)
        .then(data => {
            if (!data) {
                console.error('Datos no válidos recibidos de la API');
                createDefaultDashboardCharts(); // Usar datos predeterminados si no hay datos
                return;
            }
            
            // Crear gráficas con los datos recibidos
            if (data.consumo_horas) createHourlyChart(data.consumo_horas);
            if (data.consumo_dias) createDailyChart(data.consumo_dias);
            if (data.consumo_edificios) createBuildingChart(data.consumo_edificios);
            createTrendChart();
        })
        .catch(error => {
            console.error('Error al cargar datos del dashboard:', error);
            // Mostrar mensaje de error y cargar gráficas con datos predeterminados
            createDefaultDashboardCharts();
        });
}

/**
 * Inicializa las gráficas para el dashboard de edificios
 */
function initBuildingDashboardCharts() {
    // Intentar cargar datos de edificios desde la API
    Promise.all([
        fetchWithErrorHandling('/api/buildings/consumption', createBuildingConsumptionChart),
        fetchWithErrorHandling('/api/buildings/occupancy', createOccupancyChart),
        fetchWithErrorHandling('/api/predictions/history', createPredictionHistoryChart)
    ]).catch(error => {
        console.error('Error al inicializar dashboard de edificios:', error);
    });
}

/**
 * Inicializa las gráficas para la página de predicción
 */
function initPredictionCharts() {
    // Esta función se puede expandir según necesidades
    console.log('Inicializando gráficas de predicción');
    // Implementar según sea necesario
}

// ==================================================
// FUNCIONES AUXILIARES DE MANEJO DE DATOS
// ==================================================

/**
 * Función para manejar respuestas de la API
 */
function handleResponse(response) {
    if (!response.ok) {
        throw new Error(`Error en la respuesta: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

/**
 * Función para manejo automatizado de errores en fetch con fallback
 */
function fetchWithErrorHandling(url, successCallback, defaultCallback) {
    return fetch(url)
        .then(handleResponse)
        .then(data => {
            if (data) {
                successCallback(data);
            } else {
                console.warn(`Datos no válidos recibidos de ${url}`);
                if (defaultCallback) defaultCallback();
            }
        })
        .catch(error => {
            console.error(`Error al cargar datos de ${url}:`, error);
            if (defaultCallback) defaultCallback();
            else {
                // Extraer el ID del canvas del callback
                const callbackStr = successCallback.toString();
                const canvasIdMatch = callbackStr.match(/getElementById\(['"]([^'"]+)['"]\)/);
                const canvasId = canvasIdMatch ? canvasIdMatch[1] : null;
                
                if (canvasId) {
                    showErrorMessage(canvasId);
                }
            }
            throw error; // Propagar el error para Promise.all
        });
}

/**
 * Función para mostrar mensajes de error en gráficos
 */
function showErrorMessage(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
        const parent = canvas.parentElement;
        // Verificar si ya hay un mensaje de error
        if (!parent.querySelector('.alert-danger')) {
            const errorMsg = document.createElement('div');
            errorMsg.className = 'alert alert-danger mt-3';
            errorMsg.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-2"></i> Error al cargar los datos. Por favor, recargue la página.';
            parent.appendChild(errorMsg);
        }
    }
}

/**
 * Función para crear gráficas con datos por defecto si la API falla
 */
function createDefaultDashboardCharts() {
    // Datos de ejemplo para cada gráfica
    const hourlyData = {
        horas: Array.from({length: 24}, (_, i) => i),
        consumo: [15, 10, 8, 6, 5, 8, 12, 25, 40, 45, 50, 55, 60, 58, 52, 48, 45, 40, 35, 30, 25, 20, 18, 16]
    };
    
    const dailyData = {
        dias: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
        consumo: [45, 48, 46, 47, 42, 30, 25]
    };
    
    const buildingData = {
        edificios: ['Biblioteca', 'Administrativo', 'Ingeniería', 'Cafetería', 'Auditorio'],
        consumo: [120, 85, 150, 45, 60]
    };
    
    // Crear gráficas con datos predeterminados
    createHourlyChart(hourlyData);
    createDailyChart(dailyData);
    createBuildingChart(buildingData);
    createTrendChart();
}

// ==================================================
// FUNCIONES DE CREACIÓN DE GRÁFICAS PARA DASHBOARD PRINCIPAL
// ==================================================

/**
 * Crea la gráfica de consumo por hora del día
 */
function createHourlyChart(data) {
    // Verificar elementos necesarios
    if (!data || !data.horas || !data.consumo) {
        console.error('Datos incompletos para la gráfica horaria');
        return;
    }
    
    const canvas = document.getElementById('hourlyChart');
    if (!canvas) {
        console.error('Elemento canvas "hourlyChart" no encontrado');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    try {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.horas.map(h => `${h}:00`),
                datasets: [{
                    label: 'Consumo energético (kWh)',
                    data: data.consumo,
                    backgroundColor: 'rgba(0, 123, 255, 0.2)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointBackgroundColor: 'rgba(0, 123, 255, 1)',
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y} kWh`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Consumo (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Hora del día'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al crear gráfica horaria:', error);
        showErrorMessage('hourlyChart');
    }
}

/**
 * Crea la gráfica de consumo por día de la semana
 */
function createDailyChart(data) {
    // Verificar elementos necesarios
    if (!data || !data.dias || !data.consumo) {
        console.error('Datos incompletos para la gráfica diaria');
        return;
    }
    
    const canvas = document.getElementById('dailyChart');
    if (!canvas) {
        console.error('Elemento canvas "dailyChart" no encontrado');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    try {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.dias,
                datasets: [{
                    label: 'Consumo energético (kWh)',
                    data: data.consumo,
                    backgroundColor: [
                        'rgba(0, 123, 255, 0.7)',
                        'rgba(0, 123, 255, 0.7)',
                        'rgba(0, 123, 255, 0.7)',
                        'rgba(0, 123, 255, 0.7)',
                        'rgba(0, 123, 255, 0.7)',
                        'rgba(128, 0, 128, 0.7)',
                        'rgba(128, 0, 128, 0.7)'
                    ],
                    borderColor: [
                        'rgba(0, 123, 255, 1)',
                        'rgba(0, 123, 255, 1)',
                        'rgba(0, 123, 255, 1)',
                        'rgba(0, 123, 255, 1)',
                        'rgba(0, 123, 255, 1)',
                        'rgba(128, 0, 128, 1)',
                        'rgba(128, 0, 128, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y} kWh`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Consumo (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Día de la semana'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al crear gráfica diaria:', error);
        showErrorMessage('dailyChart');
    }
}

/**
 * Crea la gráfica de consumo por edificio
 */
function createBuildingChart(data) {
    // Verificar elementos necesarios
    if (!data || !data.edificios || !data.consumo) {
        console.error('Datos incompletos para la gráfica de edificios');
        return;
    }
    
    const canvas = document.getElementById('buildingChart');
    if (!canvas) {
        console.error('Elemento canvas "buildingChart" no encontrado');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    try {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.edificios,
                datasets: [{
                    label: 'Consumo energético (kWh)',
                    data: data.consumo,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.x} kWh`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Consumo (kWh)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al crear gráfica de edificios:', error);
        showErrorMessage('buildingChart');
    }
}

/**
 * Crea la gráfica de tendencias (últimos 6 meses)
 */
function createTrendChart() {
    const canvas = document.getElementById('trendChart');
    if (!canvas) {
        console.error('Elemento canvas "trendChart" no encontrado');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Datos simulados de tendencia
    const meses = ['Diciembre', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo'];
    const consumoReal = [520, 510, 490, 475, 465, 450];
    const consumoProyectado = [520, 510, 490, 475, 465, 430];
    
    try {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: meses,
                datasets: [
                    {
                        label: 'Consumo real',
                        data: consumoReal,
                        backgroundColor: 'rgba(0, 123, 255, 0.2)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        borderWidth: 2,
                        tension: 0.3
                    },
                    {
                        label: 'Proyección optimizada',
                        data: consumoProyectado,
                        backgroundColor: 'rgba(40, 167, 69, 0.2)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y} kWh`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Consumo mensual (kWh)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al crear gráfica de tendencias:', error);
        showErrorMessage('trendChart');
    }
}

// ==================================================
// FUNCIONES DE CREACIÓN DE GRÁFICAS PARA DASHBOARD DE EDIFICIOS
// ==================================================

/**
 * Crea la gráfica de consumo por edificio en el dashboard de edificios
 */
function createBuildingConsumptionChart(data) {
    const ctx = document.getElementById('buildingConsumptionChart').getContext('2d');
    
    try {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.buildings,
                datasets: [{
                    label: 'Consumo energético promedio (kWh)',
                    data: data.consumption,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.x} kWh`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Consumo promedio (kWh)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al crear gráfica de consumo por edificio:', error);
        showErrorMessage('buildingConsumptionChart');
    }
}

/**
 * Crea la gráfica de historial de predicciones
 */
function createPredictionHistoryChart(data) {
    const ctx = document.getElementById('predictionHistoryChart').getContext('2d');
    
    try {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: data.datasets.map((dataset, index) => {
                    // Generar colores aleatorios pero consistentes
                    const r = Math.floor((index * 137 + 50) % 200 + 55);
                    const g = Math.floor((index * 163 + 100) % 200 + 55);
                    const b = Math.floor((index * 83 + 150) % 200 + 55);
                    
                    return {
                        label: dataset.label,
                        data: dataset.data,
                        backgroundColor: `rgba(${r}, ${g}, ${b}, 0.2)`,
                        borderColor: `rgba(${r}, ${g}, ${b}, 1)`,
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 3
                    };
                })
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y} kWh`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Consumo (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Fecha'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al crear gráfica de historial de predicciones:', error);
        showErrorMessage('predictionHistoryChart');
    }
}

/**
 * Crea la gráfica de ocupación por edificio
 */
function createOccupancyChart(data) {
    const ctx = document.getElementById('occupancyChart').getContext('2d');
    
    try {
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.buildings,
                datasets: [{
                    label: 'Ocupación promedio (personas)',
                    data: data.occupancy,
                    backgroundColor: 'rgba(0, 123, 255, 0.2)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(0, 123, 255, 1)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        ticks: {
                            display: false
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.r} personas`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al crear gráfica de ocupación:', error);
        showErrorMessage('occupancyChart');
    }
}