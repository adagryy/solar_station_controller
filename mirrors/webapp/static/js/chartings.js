async function drawChart(ctx, readingInterval) {
    // Get data from server for drawin on the chart
    let dataForChart = await fetch('https://' + window.location.host + '/viewer/drawChart/');
    let responseBody = await dataForChart.json();

    // console.log(responseBody);
    let chartLabels = createXAsixLabels(responseBody, readingInterval);

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
}

function createXAsixLabels(array, readingInterval) {
    let timeArr = array.map((item) => {
        let date = new Date(item.dateOfReading);
        return date.toLocaleDateString().slice(0, 10) + " " + date.toTimeString().slice(0, 5);
    });

    let requiredNumberOfmeasurements = 288; // 24hours * 12 readings per hour.  ==> for readingInterval = 5 minutes that is:  288 = 24 * (60 / 5)
    if (array.length >= requiredNumberOfmeasurements) { // If array has all required time labels, there is no need to create empty labels (dates, which has not a readings)
        return timeArr;
    }
    let lackingElementsAmount = requiredNumberOfmeasurements - timeArr.length // We estimate how much readings are lacking
    let lackingElements = [] // Array for storing lacking dates of readings
    let startingDate = new Date(array[0].dateOfReading); // Create date from which we are starting countdown

    for (i = 0; i < lackingElementsAmount; i++) {
        let currentDate = new Date(startingDate.setMinutes(startingDate.getMinutes() - readingInterval)); // Get next date, which has not assigned any temperature reading
        lackingElements.push(currentDate.toLocaleDateString().slice(0, 10) + " " + currentDate.toTimeString().slice(0, 5)); // ...and store it in array
    }
    return (lackingElements.reverse()).concat(timeArr); // Reverse order of array with lacking date labels and join it with labels, which already have a readings. 
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