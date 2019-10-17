async function drawChart(ctx) {
    // Get data from server for drawin on the chart
    let dataForChart = await fetch('https://' + window.location.host + '/viewer/drawChart/');
    let responseBody = await dataForChart.json();

    // console.log(responseBody);
    let chartLabels = createXAsixLabels(responseBody);
    let chartData = generateDataForCharts(responseBody);

    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            "labels": chartLabels,
            "datasets": [{
                label: 'Czujnik lewy',
                // backgroundColor: 'Green',
                fill: false,
                borderColor: 'DarkGreen',
                data: chartData.leftSensorReadings
            }, {
                label: 'Czujnik środkowy',
                // backgroundColor: 'Green',
                fill: false,
                borderColor: 'Orange',
                data: chartData.middleSensorReadings
            }, {
                label: 'Czujnik prawy',
                // backgroundColor: 'Green',
                fill: false,
                borderColor: 'yellow',
                data: chartData.rightSensorReadings
            }, {
                label: 'Czujnik w zbiorniku',
                backgroundColor: 'DarkRed',
                borderColor: 'Red',
                data: chartData.tankSensorReadings
            }]
        },
        options: {
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
}

function createXAsixLabels(array) {
    return array.map((item) => {
        return new Date(item.dateOfReading).toTimeString().slice(0, 5)
    });
}

function generateDataForCharts(array) {
    let leftSensorReadings = [],
        middleSensorReadings = [],
        rightSensorReadings = [],
        tankSensorReadings = [];
    array.forEach((item) => {
        leftSensorReadings.push(Math.round(item.leftSensorTemperature));
        middleSensorReadings.push(item.middleSensorTemperature);
        rightSensorReadings.push(item.rightSensorTemperature);
        tankSensorReadings.push(item.tankSensorTemperature);
    });
    return { leftSensorReadings, middleSensorReadings, rightSensorReadings, tankSensorReadings }
}