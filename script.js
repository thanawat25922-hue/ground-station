document.addEventListener("DOMContentLoaded", function(){

/* ===== CHART ===== */

const altChart = new Chart(
document.getElementById('altChart'),{
    type:'line',
    data:{
        labels:[],
        datasets:[{
            label:'Altitude (m)',
            data:[],
            borderColor:'#00ffaa',
            tension:0.3
        }]
    },
    options:{
        animation:false,
        scales:{
            y:{
                ticks:{
                    color:'white',
                    font:{size:14}
                }
            },
            x:{
                ticks:{color:'white'}
            }
        },
        plugins:{
            legend:{
                labels:{
                    color:'white',
                    font:{size:14}
                }
            }
        }
    }
});

/* ===== MAP ===== */

let map = L.map('map').setView([13.731995,100.775850],15);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{maxZoom:19}
).addTo(map);

let marker = L.marker([13.731995,100.775850]).addTo(map);

/* ===== DEMO DATA ===== */

let t=0;

setInterval(()=>{

    t++;

    let altitude = 170 + Math.sin(t/3)*15;
    let temp = 25 + Math.sin(t/5)*2;
    let voltage = 7 + Math.sin(t/4)*0.3;
    let pressure = 1000 + Math.sin(t/6)*5;

    let lat = 13.731995 + Math.sin(t/20)*0.001;
    let lon = 100.775850 + Math.cos(t/20)*0.001;

    document.getElementById("packet").innerText = t;
    document.getElementById("altitude").innerText = altitude.toFixed(1);
    document.getElementById("temp").innerText = temp.toFixed(1);
    document.getElementById("voltage").innerText = voltage.toFixed(2);
    document.getElementById("pressure").innerText = pressure.toFixed(1);
    document.getElementById("lat").innerText = lat.toFixed(6);
    document.getElementById("lon").innerText = lon.toFixed(6);

    if(altChart.data.labels.length>30){
        altChart.data.labels.shift();
        altChart.data.datasets[0].data.shift();
    }

    altChart.data.labels.push("");
    altChart.data.datasets[0].data.push(altitude);
    altChart.update();

    marker.setLatLng([lat,lon]);

},1000);

});
