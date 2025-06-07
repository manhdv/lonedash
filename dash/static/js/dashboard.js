document.addEventListener("DOMContentLoaded", function () {
  fetch("/api/portfolio/data/")
    .then(res => res.json())
    .then(data => {
      const ctx = document.getElementById('myChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [
            {
              label: 'Principal',
              data: data.principal,
              borderColor: 'blue',
              fill: false,
              pointRadius: 0

            },
            {
              label: 'Equity',
              data: data.equity,
              borderColor: 'green',
              fill: false,
              pointRadius: 0
            }
          ]
        }
      });
    });
});
