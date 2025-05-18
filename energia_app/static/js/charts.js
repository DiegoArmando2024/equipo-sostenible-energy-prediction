// Archivo consolidado de gráficos - consolidated_charts.js

document.addEventListener('DOMContentLoaded', function() {
    // Verificar si los elementos existen antes de crear los gráficos
    initializeAllCharts();
});

// Función de inicialización principal
function initializeAllCharts() {
    // Gráficos de Dashboard
    if (document.getElementById('hourlyChart')) {
        fetchDashboardData();
    }
    
    // Gráficos específicos de edificios
    if (document.getElementById('buildingConsumptionChart')) {
        createBuildingConsumptionChart();
    }
    
    if (document.getElementById('predictionHistoryChart')) {
        createPredictionHistoryChart();
    }
    
    if (document.getElementById('occupancyChart')) {
        createOccupancyChart();
    }
}

// Función para obtener datos del dashboard principal
function fetchDashboardData() {
    fetch('/api/data')
        .then(handleResponse)
        .then(data => {
            if (!data) {
                console.error('Datos no válidos recibidos de la API');
                return;
            }
            
            if (data.consumo_horas) createHourlyChart(data.consumo_horas);
            if (data.consumo_dias) createDailyChart(data.consumo_dias);
            if (data.consumo_edificios) createBuildingChart(data.consumo_edificios);
            createTrendChart();
        })
        .catch(handleError);
}

// Función auxiliar para manejar respuestas
function handleResponse(response) {
    if (!response.ok) {
        throw new Error(`Error en la respuesta: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

// Función auxiliar para manejar errores
function handleError(error) {
    console.error('Error al cargar datos:', error);
    document.querySelectorAll('.card-body canvas').forEach(canvas => {
        const parent = canvas.parentElement;
        const errorMsg = document.createElement('div');
        errorMsg.className = 'alert alert-danger';
        errorMsg.textContent = 'Error al cargar los datos. Por favor, recargue la página.';
        parent.appendChild(errorMsg);
    });
}

// ==========================================
// GRÁFICOS DEL DASHBOARD PRINCIPAL
// ==========================================

// Gráfica de consumo por hora del día
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
                maintainAspectRatio: false,
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
    }
}

// Gráfica de consumo por día de la semana
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
                maintainAspectRatio: false,
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
    }
}

// Gráfica de consumo por edificio
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
                maintainAspectRatio: false,
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
    }
}

// Gráfica de tendencias (últimos 6 meses)
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
                maintainAspectRatio: false,
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
    }
}

// ==========================================
// GRÁFICOS DEL DASHBOARD DE EDIFICIOS
// ==========================================

// Obtener datos de consumo por edificio
function createBuildingConsumptionChart() {
    fetch('/api/buildings/consumption')
        .then(handleResponse)
        .then(data => {
            const ctx = document.getElementById('buildingConsumptionChart').getContext('2d');
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
                    maintainAspectRatio: false,
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
        })
        .catch(error => {
            console.error('Error al cargar datos de consumo por edificio:', error);
            showErrorMessage('buildingConsumptionChart');
        });
}

// Gráfico de predicción histórica
function createPredictionHistoryChart() {
    fetch('/api/predictions/history')
        .then(handleResponse)
        .then(data => {
            const ctx = document.getElementById('predictionHistoryChart').getContext('2d');
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
                    maintainAspectRatio: false,
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
        })
        .catch(error => {
            console.error('Error al cargar historial de predicciones:', error);
            showErrorMessage('predictionHistoryChart');
        });
}

// Gráfico de ocupación por edificio
function createOccupancyChart() {
    fetch('/api/buildings/occupancy')
        .then(handleResponse)
        .then(data => {
            const ctx = document.getElementById('occupancyChart').getContext('2d');
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
                    maintainAspectRatio: false,
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
        })
        .catch(error => {
            console.error('Error al cargar datos de ocupación:', error);
            showErrorMessage('occupancyChart');
        });
}

// Función auxiliar para mostrar mensajes de error en gráficos
function showErrorMessage(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
        const parent = canvas.parentElement;
        const errorMsg = document.createElement('div');
        errorMsg.className = 'alert alert-danger';
        errorMsg.textContent = 'Error al cargar los datos. Por favor, recargue la página.';
        parent.appendChild(errorMsg);
    }
}