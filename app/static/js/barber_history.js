// Barber History Page Script

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Get chart data from data attributes on the canvas
    const canvas = document.getElementById('commissionChart');
    if (canvas) {
        const labels = canvas.dataset.labels ? JSON.parse(canvas.dataset.labels) : [];
        const commissionData = canvas.dataset.commission ? JSON.parse(canvas.dataset.commission) : [];
        
        if (labels.length && commissionData.length) {
            const ctx = canvas.getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Commission (GH₵)',
                        data: commissionData,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Amount (GH₵)' }
                        },
                        x: {
                            title: { display: true, text: 'Month' }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return 'GH₵' + context.raw.toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        } else {
            console.warn('Chart data missing');
            canvas.parentElement.innerHTML = '<div class="alert alert-info">No data available for chart.</div>';
        }
    }
});