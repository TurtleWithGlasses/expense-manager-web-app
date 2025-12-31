/**
 * Category Bar Chart - Chart.js Integration
 *
 * Creates horizontal bar chart for category comparison
 * Perfect for ranking categories by spending amount
 */

function createCategoryBarChart(containerId, data) {
    const ctx = document.getElementById(containerId);

    if (!ctx) {
        console.error(`Container ${containerId} not found`);
        return null;
    }

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.categories || [],
            datasets: [{
                label: 'Spending',
                data: data.amounts || [],
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
                hoverBackgroundColor: 'rgba(59, 130, 246, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y', // Horizontal bars
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '$' + value.toFixed(0)
                    },
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: ctx => '$' + ctx.parsed.x.toFixed(2)
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const categoryIndex = elements[0].index;
                    const categoryName = data.categories[categoryIndex];
                    const categoryId = data.category_ids ? data.category_ids[categoryIndex] : categoryIndex;

                    if (data.onCategoryClick) {
                        data.onCategoryClick(categoryId, categoryName);
                    }
                }
            }
        }
    });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createCategoryBarChart };
}
