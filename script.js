// =======================
// MAP
// =======================
let map = L.map('map').setView([13.731995, 100.775850], 17);

L.tileLayer(
 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map);

let marker = L.marker([13.731995, 100.775850]).addTo(map);

// =======================
// CHART ALTITUDE
// =======================
const altChart = new Chart(
document.getElementById('altChart'),
{
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Altitude',
            data: [],
            borderColor: '#00ffaa',
            tension: 0.2
        }]
    },
    options: {
        animation:false,
        scales: {
            x: { display:false }
        }
    }
});

// =======================
// CHART TEMP
// =======================
const tempChart = new Chart(
document.getElementById('tempChart'),
{
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Temperature',
            data: [],
            borderColor: '#ff5555',
            tension: 0.2
        }]
    },
    options: {
        animation:false,
        scales: {
            x: { display:false }
        }
    }
});

// =======================
// SIMULATED TELEMETRY
// =======================
let packet = 0;

setInterval(() => {

    packet++;

    let data = {
        team: "G2",
        packet: packet,
        volt: (7.2 + Math.random()).toFixed(2),
        alt: (170 + Math.random()*20).toFixed(1),
        temp: (24 + Math.random()*3).toFixed(1),
        hum: (40 + Math.random()*10).toFixed(1),
        lat: 13.731995 + Math.random()*0.0003,
        lon: 100.775850 + Math.random()*0.0003
    };

    // update text
    document.getElementById("team").innerText = data.team;
    document.getElementById("packet").innerText = data.packet;
    document.getElementById("volt").innerText = data.volt;
    document.getElementById("alt").innerText = data.alt;
    document.getElementById("temp").innerText = data.temp;
    document.getElementById("hum").innerText = data.hum;
    document.getElementById("lat").innerText = data.lat.toFixed(6);
    document.getElementById("lon").innerText = data.lon.toFixed(6);

    document.getElementById("status").style.background = "lime";

    // update chart
    altChart.data.labels.push("");
    altChart.data.datasets[0].data.push(data.alt);

    tempChart.data.labels.push("");
    tempChart.data.datasets[0].data.push(data.temp);

    if (altChart.data.labels.length > 30) {
        altChart.data.labels.shift();
        altChart.data.datasets[0].data.shift();
        tempChart.data.labels.shift();
        tempChart.data.datasets[0].data.shift();
    }

    altChart.update();
    tempChart.update();

    // update map
    marker.setLatLng([data.lat, data.lon]);
    map.panTo([data.lat, data.lon]);

}, 1000);
