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

function dayInYear(element, element_label, any, any_label, latitude, longitude = 21.91, now = new Date()) {
    let start = new Date(now.getFullYear(), 0, 0); // First day of current year
    let diff = (now - start) + ((start.getTimezoneOffset() - now.getTimezoneOffset()) * 60 * 1000); // Calculate, how many miliseconds left from beginning of the year 
    let oneDay = 1000 * 60 * 60 * 24; // day in miliseconds <==> 24hours * 60 minutes* 60 seconds * 1000 miliseconds
    let N = Math.floor(diff / oneDay); // Day of year
    let rad = (degrees) => { return degrees * (Math.PI / 180); } // Converts degrees to radians
    let deg = (radians) => { return (180 * radians) / Math.PI; } // Converts radians to degrees
    let angle = -deg(Math.asin((0.39779 * Math.cos(rad(0.98565 * (N + 10) + 1.914 * Math.sin(rad(0.98565 * (N - 2)))))))); // Formula for evaluating the angle between the rays of the Sun and the plane of the Earth's equator; https://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations
    let noon_sun_declination = 90 - latitude + angle; // Angle of rays in noon relative to the local (given by both longitude and latitude) earth surface
    element_label.innerHTML = `Kąt padania promieni słonecznych w południe (52&#176;N, ` + now.toLocaleDateString().slice(0, 10) + `)`;
    element.innerHTML = (Math.round(noon_sun_declination * 100) / 100).toString() + ` &#176;`;

    // Calculate angle between zenith and point of measurement
    // Use dot product


    // Calculates difference in minutes from current UTC time to UTC noon and is calculated separately for western and eastern Earth hemisphere.
    // The range of "dateDifferenceInMinutes" is from range: <0, 720> minutes (for Sun zenithing longitudes from range 0 degrees W to 180 degrees W and separately for Sun zenithing longitudes from range 180 degrees E to 0 degrees E), NOT <0, 1440> minutes
    // For instance if current UTC time is 14:08 UTC, then "dateDifferenceInMinutes" will be 128 minutes.
    // But for 9:52 UTC it will also be 128 minutes.
    let dateDifferenceInMinutes = Math.round((Math.abs(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds()) -
        Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 12, 0, now.getUTCSeconds()))) / 60000);

    // Below we are calculating the current longitude of the point where the Sun is in zenith.
    // For instance if the current time is 11:00 UTC, then the "dateDifferenceInMinutes" is equal to 60 minutes
    let currentZenithalSunLongitude = dateDifferenceInMinutes / 4; // Earth rotates 1 degree per 4 minutes.

    // If current time is after UTC noon (Sun zenith is on western hemisphere), then we assume Sun longitude is negative to simplify calculations
    // Now we can easily calculate difference between longitude of Sun zenith point and the longitude of the point of measurement.
    if (now.getUTCHours() >= 12) {
        currentZenithalSunLongitude *= -1;
    }      


    let final = calculateAngleBetweenVectors(currentZenithalSunLongitude, angle, longitude, latitude);
    let openingAngle = 90 - final;
    // console.log("Dlugosc slonca: : " + currentZenithalSunLongitude + " Moja dlugosc: " + longitude)
    any_label.innerHTML = `Kąt padania promieni słonecznych (godzina: ` + now.toTimeString().slice(0,8) + `, szerokość geogr: ` + latitude + `&#176;N, ` + now.toLocaleDateString().slice(0, 10) + `)`;
    any.innerHTML = (Math.round(openingAngle*100)/100).toString() + ` &#176;`;

    // // Suppose, that the point of measurement is the place on the Earth where you want to measure angle of sun rays incidence.
    // // Below K1 is the angle between two lines: 1). the line starting in Earth center and passing through the point of measurement and...
    // // 2). the line starting in Earth center and passing through the point where the sun is in zenith (sun noon in the point of measurement). Please notice, that these points HAVE THE SAME LONGITUDE (BOTH ARE ON THE SAME MERIDIAN).
    // // For instance if there is 22th June and your position is the latitude 52 degrees N, then the sun zenith is on latitude 23 degress N. So K1 variable will be as follows: K1 = 52 - 23 = 29 degrees
    // let K1 = Math.abs(latitude - angle); // Absolute value is used to make K1 positive, when latitude is southern and "angle" is also southern. For instance: -45 degrees S -(-12) degress S

    // // Similarly K2 is the angle between current Sun zenith longitude (notice Sun zenith longitude changes 1 degree every 4 minutes) and the longitude of the K1 point (which in fact is the longitude of the point of measurement). 
    // // Notice that these points HAVE THE SAME LATITUDE.
    // // For instance if current time local time is 14:08 UTC (15:08 CET, 16:08 CEST [14:08 UTC is 128 minutes after 12:00 UTC]), then the Sun zenith longitude will be 32 degrees W (128 / 4 = 32).
    // // Then supposing that the longitude of the point of measurement is 21.92 degrees E, then K2 is: K2 = 32 degrees W + 21.92 degrees W = 53.92 degrees (in calculations we do operation: 21.92 - (-32) = 53.92)
    // // But above we have calculated "dateDifferenceInMinutes" 
    // let K2 = calculateK2(longitude, currentZenithalSunLongitude);

    // // if(K2 > 90) {
    // //   K2 = 90;
    // // }

    // // Final angle of Sun rays incidence on Earth in the point of measurement
    // let final = 90 - deg(Math.acos(Math.cos(rad(K1)) + Math.cos(rad(K2)) - 1));

    // let refracted = 1.02 * ctg(final + (10.3/(final+5.11)));

    // // console.log("Różnica: " + K2);
    // console.log('Godzina UTC: ' + now.toISOString().slice(11, 19) + ', Godzina LOK: ' + localNow.toTimeString().slice(0,8) + ', Ostateczny wynik: ' + Math.round(final) 
    //   + ', K1: ' + Math.round(K1) + ', K2: ' + Math.round(K2) + ', Różnica: ' + dateDifferenceInMinutes + ', Sun long: ' 
    //   + Math.round(currentZenithalSunLongitude) + ', Rozwarcie: ' + Math.round(deg(Math.acos(Math.cos(rad(K1)) + Math.cos(rad(K2)) - 1)))
    //   + ', zenit: ' + Math.round(angle) + '; ' + currentZenithalSunLongitude + ", Refracted: " + deg(refracted));
    // let hhmm_now = now.toTimeString().slice(0, 5);
    // console.log(angle + ", " + currentZenithalSunLongitude + "")
}

function calculateAngleBetweenVectors(sunLongitude, sunLatitude, longitude, latitude) {  
  let R = 6371; 
  let rad = (degrees) => { return degrees * (Math.PI / 180); } // Converts degrees to radians
  let deg = (radians) => { return (180 * radians) / Math.PI; } // Converts radians to degrees
  let zenith = {
      x: R * Math.cos(rad(sunLatitude)) * Math.cos(rad(sunLongitude)),
      y: R * Math.cos(rad(sunLatitude)) * Math.sin(rad(sunLongitude)),
      z: R * Math.sin(rad(sunLatitude))
    },
    point = {
      x: R * Math.cos(rad(latitude)) * Math.cos(rad(longitude)),
      y: R * Math.cos(rad(latitude)) * Math.sin(rad(longitude)),
      z: R * Math.sin(rad(latitude))
    }
  let dotProduct = point.x*zenith.x + point.y*zenith.y + point.z*zenith.z;
  let lengthProduct = Math.sqrt(point.x**2 + point.y**2 + point.z**2) * Math.sqrt(zenith.x**2 + zenith.y**2 + zenith.z**2);
  return deg(Math.acos(dotProduct / lengthProduct));
}

function drawSunriseSunset(ctx) {
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
  
  return myChart;
}