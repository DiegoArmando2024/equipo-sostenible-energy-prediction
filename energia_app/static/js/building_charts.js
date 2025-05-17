// Obtener datos de consumo por edificio
function createBuildingConsumptionChart() {
    fetch('/api/buildings/consumption')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error en la respuesta: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
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
            const canvas = document.getElementById('buildingConsumptionChart');
            const parent = canvas.parentElement;
            const errorMsg = document.createElement('div');
            errorMsg.className = 'alert alert-danger';
            errorMsg.textContent = 'Error al cargar los datos. Por favor, recargue la página.';
            parent.appendChild(errorMsg);
        });
}

// Gráfico de predicción histórica
function createPredictionHistoryChart() {
    fetch('/api/predictions/history')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error en la respuesta: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
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
            const canvas = document.getElementById('predictionHistoryChart');
            const parent = canvas.parentElement;
            const errorMsg = document.createElement('div');
            errorMsg.className = 'alert alert-danger';
            errorMsg.textContent = 'Error al cargar los datos. Por favor, recargue la página.';
            parent.appendChild(errorMsg);
        });
}

// Gráfico de ocupación por edificio
function createOccupancyChart() {
    fetch('/api/buildings/occupancy')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error en la respuesta: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
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
            const canvas = document.getElementById('occupancyChart');
            const parent = canvas.parentElement;
            const errorMsg = document.createElement('div');
            errorMsg.className = 'alert alert-danger';
            errorMsg.textContent = 'Error al cargar los datos. Por favor, recargue la página.';
            parent.appendChild(errorMsg);
        });
}

// Inicializar todos los gráficos
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si los elementos existen antes de crear los gráficos
    if (document.getElementById('buildingConsumptionChart')) {
        createBuildingConsumptionChart();
    }
    
    if (document.getElementById('predictionHistoryChart')) {
        createPredictionHistoryChart();
    }
    
    if (document.getElementById('occupancyChart')) {
        createOccupancyChart();
    }
});