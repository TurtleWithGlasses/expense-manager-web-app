/**
 * Category Pie Chart - Chart.js Integration
 *
 * Creates interactive doughnut chart for category breakdown
 * with drill-down capabilities and percentage tooltips
 */

function createCategoryPieChart(containerId, data) {
    const ctx = document.getElementById(containerId);

    if (!ctx) {
        console.error(`Container ${containerId} not found`);
        return null;
    }

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.categories || [],
            datasets: [{
                data: data.amounts || [],
                backgroundColor: data.colors || [
                    '#ef4444', // red
                    '#3b82f6', // blue
                    '#10b981', // green
                    '#f59e0b', // amber
                    '#8b5cf6', // purple
                    '#ec4899', // pink
                    '#14b8a6', // teal
                    '#f97316', // orange
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                        }
                    },
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    // Drill down to category details
                    const categoryIndex = elements[0].index;
                    const categoryName = data.categories[categoryIndex];
                    const categoryId = data.category_ids ? data.category_ids[categoryIndex] : categoryIndex;

                    if (data.onCategoryClick) {
                        data.onCategoryClick(categoryId, categoryName);
                    } else {
                        // Default: navigate to category details
                        window.location.href = `/categories/${categoryId}/details`;
                    }
                }
            }
        }
    });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createCategoryPieChart };
}
