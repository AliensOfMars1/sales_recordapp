// CEO Dashboard - Chart.js initialization
document.addEventListener('DOMContentLoaded', function() {
    
    // Dashboard Profit Chart
    const profitCanvas = document.getElementById('profitChart');
    if (profitCanvas && profitCanvas.dataset.labels && profitCanvas.dataset.profits) {
        try {
            const labels = JSON.parse(profitCanvas.dataset.labels);
            const profits = JSON.parse(profitCanvas.dataset.profits);
            new Chart(profitCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Net Profit (GH₵)',
                        data: profits,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, title: { display: true, text: 'Amount (GH₵)' } }
                    }
                }
            });
        } catch(e) { console.error('Profit chart error:', e); }
    }

    // Expense Analysis - Monthly Chart
    const monthlyCanvas = document.getElementById('monthlyExpenseChart');
    if (monthlyCanvas && monthlyCanvas.dataset.months && monthlyCanvas.dataset.expenses) {
        try {
            const months = JSON.parse(monthlyCanvas.dataset.months);
            const expenses = JSON.parse(monthlyCanvas.dataset.expenses);
            new Chart(monthlyCanvas, {
                type: 'bar',
                data: {
                    labels: months,
                    datasets: [{
                        label: 'Expenses (GH₵)',
                        data: expenses,
                        backgroundColor: '#dc3545'
                    }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
        } catch(e) { console.error('Monthly chart error:', e); }
    }

    // Expense Analysis - Category Chart
    const categoryCanvas = document.getElementById('categoryChart');
    if (categoryCanvas && categoryCanvas.dataset.categories && categoryCanvas.dataset.amounts) {
        try {
            const categories = JSON.parse(categoryCanvas.dataset.categories);
            const amounts = JSON.parse(categoryCanvas.dataset.amounts);
            new Chart(categoryCanvas, {
                type: 'pie',
                data: {
                    labels: categories,
                    datasets: [{
                        data: amounts,
                        backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40']
                    }]
                },
                options: { responsive: true }
            });
        } catch(e) { console.error('Category chart error:', e); }
    }

    // Yearly Profit Chart
    const yearlyCanvas = document.getElementById('yearlyProfitChart');
    if (yearlyCanvas && yearlyCanvas.dataset.years && yearlyCanvas.dataset.profits) {
        try {
            const years = JSON.parse(yearlyCanvas.dataset.years);
            const profits = JSON.parse(yearlyCanvas.dataset.profits);
            new Chart(yearlyCanvas, {
                type: 'bar',
                data: {
                    labels: years,
                    datasets: [{
                        label: 'Net Profit (GH₵)',
                        data: profits,
                        backgroundColor: '#28a745'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, title: { display: true, text: 'Amount (GH₵)' } }
                    }
                }
            });
        } catch(e) { console.error('Yearly chart error:', e); }
    }
});