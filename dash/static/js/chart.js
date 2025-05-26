// Chart theme config - dùng lại được
const chartTheme = {
    layout: {
        background: { color: '#111' },
        textColor: '#eee',
    },
    grid: {
        vertLines: { color: '#222' },
        horzLines: { color: '#222' },
    },
};

function createResponsiveChart(containerId, seriesData) {
    const container = document.getElementById(containerId);
    const resizeChart = () => {
        const style = getComputedStyle(container);
        const paddingX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
        const paddingY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
        const width = container.clientWidth - paddingX;
        const height = container.clientHeight - paddingY;
        chart.resize(width, height);
    };

    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: container.clientHeight,
        ...chartTheme,
    });

    const lineSeries = chart.addSeries(LightweightCharts.LineSeries);
    lineSeries.setData(seriesData);

    window.addEventListener('resize', resizeChart);
    resizeChart();

    return chart;
}

