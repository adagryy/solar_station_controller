async function drawChart(ctx, xDomain) {
    // Get data from server for drawin on the chart
    let dataForChart = await fetch('https://' + window.location.host + '/viewer/drawChart/');
    let responseBody = await dataForChart.json();

    let resetRef = function() {
        myChart.destroy();
    }

    let chartLabels = [], chartData = [];
    if (responseBody.length > 0) {
        chartLabels = createXAsixLabels(responseBody);
        chartData = generateDataForCharts(responseBody);

        if (xDomain < 24) {
            chartLabels = chartLabels.slice(-xDomain * 12); // xDomain - is a number of hours to be displayed on x axis
            chartData.leftSensorReadings = chartData.leftSensorReadings.slice(-xDomain * 12);
            chartData.middleSensorReadings = chartData.middleSensorReadings.slice(-xDomain * 12);
            chartData.rightSensorReadings = chartData.rightSensorReadings.slice(-xDomain * 12);
            chartData.tankSensorReadings = chartData.tankSensorReadings.slice(-xDomain * 12);
        }
    }

    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            "labels": chartLabels,
            "datasets": [{
                label: 'Czujnik lewy',
                // backgroundColor: 'Green',
                fill: false,
                borderColor: 'DarkGreen',
                data: chartData.leftSensorReadings || []
            }, {
                label: 'Czujnik środkowy',
                // backgroundColor: 'Green',
                fill: false,
                borderColor: 'Orange',
                data: chartData.middleSensorReadings || []
            }, {
                label: 'Czujnik prawy',
                // backgroundColor: 'Green',
                fill: false,
                borderColor: 'yellow',
                data: chartData.rightSensorReadings || []
            }, {
                label: 'Czujnik w zbiorniku',
                backgroundColor: 'DarkRed',
                borderColor: 'Red',
                data: chartData.tankSensorReadings || []
            }]
        },
        options: {
            elements: {
                line: {
                    tension: 0 // disables bezier curves
                }
            },
            responsive: true,
            scales: {
                xAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Godzina'
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Temperatura'
                    }
                }]
            }
        }
    });

    return resetRef.bind(this);
}

function createXAsixLabels(array) {
    return array.map((item) => {
        let date = new Date(item.dateOfReading);
        return date.toLocaleDateString().slice(0, 10) + " " + date.toTimeString().slice(0, 5);
    });
}

function generateDataForCharts(array) {
    let leftSensorReadings = [],
        middleSensorReadings = [],
        rightSensorReadings = [],
        tankSensorReadings = [];
    array.forEach((item) => {
        let readingDate = new Date(item.dateOfReading);
        let formattedDate = readingDate.toLocaleDateString().slice(0, 10) + " " + readingDate.toTimeString().slice(0, 5);
        leftSensorReadings.push({ x: formattedDate, y: item.leftSensorTemperature });
        middleSensorReadings.push({ x: formattedDate, y: item.middleSensorTemperature });
        rightSensorReadings.push({ x: formattedDate, y: item.rightSensorTemperature });
        tankSensorReadings.push({ x: formattedDate, y: item.tankSensorTemperature });
    });
    return { leftSensorReadings, middleSensorReadings, rightSensorReadings, tankSensorReadings }
}