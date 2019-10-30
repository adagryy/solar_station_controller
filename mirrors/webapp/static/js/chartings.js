async function drawChart(ctx, xDomain) {
    // Get data from server for drawin on the chart
    let dataForChart = await fetch('https://' + window.location.host + '/viewer/drawChart/');
    let responseBody = await dataForChart.json();

    let resetRef = function() {
        myChart.destroy();
    }

    let chartLabels = [],
        chartData = [];
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

function dayInYear(element, element_label, latitude) {
    let now = new Date();
    let start = new Date(now.getFullYear(), 0, 0);
    let diff = (now - start) + ((start.getTimezoneOffset() - now.getTimezoneOffset()) * 60 * 1000);
    let oneDay = 1000 * 60 * 60 * 24;
    let N = Math.floor(diff / oneDay); // Day of year
    let rad = (degrees) => { return degrees * (Math.PI / 180); } // Converts degrees to radians
    let deg = (radians) => { return (180 * radians) / Math.PI; } // Converts radians to degrees
    let rays_angle = 90 - latitude - deg(Math.asin((0.39779 * Math.cos(rad(0.98565 * (N + 10) + 1.914 * Math.sin(rad(0.98565 * (N - 2)))))))); // Formula for evaluating the angle between the rays of the Sun and the plane of the Earth's equator; https://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations
    element_label.innerHTML = `Kąt padania promieni słonecznych w południe (52&#176;N, ` + now.toLocaleDateString().slice(0, 10) + `)`;
    element.innerHTML = (Math.round(rays_angle * 100) / 100).toString() + ` &#176;`;
}