document.addEventListener("DOMContentLoaded", function () {
  fetch("/api/portfolio/data/")
    .then(res => res.json())
    .then(data => {
      const ctx = document.getElementById('myChart').getContext('2d');

      // Tạo màu cho cột: xanh lá nếu >= 0, đỏ nếu âm
      const barColors = data.transactions.map(v => v >= 0 ? 'rgba(0, 119, 0, 0.6)' : 'rgba(200, 0, 0, 0.6)');

      new Chart(ctx, {
        data: {
          labels: data.labels,
          datasets: [
            {
              type: 'line',
              label: 'Principal',
              data: data.principal,
              borderColor: 'blue',
              fill: false,
              pointRadius: 0,
              pointHoverRadius: 0,
              yAxisID: 'y',
            },
            {
              type: 'line',
              label: 'Equity',
              data: data.equity,
              borderColor: 'green',
              fill: false,
              pointRadius: 0,
              pointHoverRadius: 0,
              yAxisID: 'y',
            },
            {
              type: 'bar',
              label: 'Transaction',
              data: data.transactions,
              backgroundColor: barColors,
              yAxisID: 'y',
              order: 0,  // để bar nằm sau line
            }
          ]
        },
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: 'Value' }
            }
          }
        }
      });
    });
});
