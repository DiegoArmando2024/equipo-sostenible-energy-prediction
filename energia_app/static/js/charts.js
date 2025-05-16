document.addEventListener('DOMContentLoaded', function() {
    // Obtener datos de la API
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            // Crear gráficas con los datos recibidos
            createHourlyChart(data.consumo_horas);
            createDailyChart(data.consumo_dias);
            createBuildingChart(data.consumo_edificios);
            createTrendChart();
        })
        .catch(error => console.error('Error al cargar datos:', error));
});

// Gráfica de consumo por hora del día
function createHourlyChart(data) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');
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
}

// Gráfica de consumo por día de la semana
function createDailyChart(data) {
    const ctx = document.getElementById('dailyChart').getContext('2d');
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
}

// Gráfica de consumo por edificio
function createBuildingChart(data) {
    const ctx = document.getElementById('buildingChart').getContext('2d');
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
}

// Gráfica de tendencias (últimos 6 meses)
function createTrendChart() {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    // Datos simulados de tendencia
    const meses = ['Diciembre', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo'];
    const consumoReal = [520, 510, 490, 475, 465, 450];
    const consumoProyectado = [520, 510, 490, 475, 465, 430];
    
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
}