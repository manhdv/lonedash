document.addEventListener("DOMContentLoaded", function () {
  fetch("/api/holdings/data/")
    .then(res => res.json())
    .then(data => {
      const ctx = document.getElementById("holdingsEquityChart").getContext("2d");

      const datasets = Object.entries(data.datasets).map(([name, values]) => ({
        label: name,
        data: values,
        borderWidth: 2,
        fill: false,
      }));

      new Chart(ctx, {
        type: "line",
        data: {
          labels: data.labels,
          datasets: datasets,
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: true }
          }
        }
      });
    })
    .catch(err => {
      console.error("Error loading chart data:", err);
    });
});