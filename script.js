document.addEventListener("DOMContentLoaded", function(){

function createChart(id,label,unit,color){

    return new Chart(document.getElementById(id),{
        type:'line',
        data:{
            labels:[],
            datasets:[{
                label: label + " ("+unit+")",
                data:[],
                borderColor:color,
                tension:0.3
            }]
        },
        options:{
            animation:false,
            responsive:true,
            scales:{
                x:{
                    ticks:{color:'white'}
                },
                y:{
                    ticks:{
                        color:'white',
                        font:{size:14}
                    },
                    title:{
                        display:true,
                        text:unit,
                        color:'white'
                    }
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
}

const altChart = createChart('altChart','Altitude','m','#00ffaa');
const tempChart = createChart('tempChart','Temperature','°C','#ff5555');
const voltChart = createChart('voltChart','Voltage','V','#ffaa00');
const pressChart = createChart('pressChart','Pressure','hPa','#55aaff');

function pushData(chart,value){
    if(chart.data.labels.length>30){
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.data.labels.push("");
    chart.data.datasets[0].data.push(value);
    chart.update();
}

/* MAP */
let map = L.map('map').setView([13.731995,100.775850],15);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{maxZoom:19}
).addTo(map);

let marker = L.marker([13.731995,100.775850]).addTo(map);

/* DEMO DATA */

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

    pushData(altChart,altitude);
    pushData(tempChart,temp);
    pushData(voltChart,voltage);
    pushData(pressChart,pressure);

    marker.setLatLng([lat,lon]);

},1000);

});
