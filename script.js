function createChart(id,label,color){
    return new Chart(
        document.getElementById(id),
        {
            type:'line',
            data:{
                labels:[],
                datasets:[{
                    label:label,
                    data:[],
                    borderColor:color,
                    tension:0.4
                }]
            },
            options:{
                animation:false,
                responsive:true,
                scales:{
                    x:{display:false},
                    y:{ticks:{color:'white'}}
                },
                plugins:{
                    legend:{labels:{color:'white'}}
                }
            }
        }
    );
}

const altChart = createChart('altChart','Altitude','#00ffaa');
const tempChart = createChart('tempChart','Temperature','#ff5555');
const voltChart = createChart('voltChart','Voltage','#ffaa00');
const pressChart = createChart('pressChart','Pressure','#55aaff');

function pushData(chart,value){

    if(chart.data.labels.length > 30){
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.data.labels.push("");
    chart.data.datasets[0].data.push(value);
    chart.update();
}

/* ===== DEMO DATA (ยังไม่ต่อ Arduino) ===== */

let t = 0;

setInterval(()=>{

    t++;

    let altitude = 170 + Math.sin(t/3)*15;
    let temp = 25 + Math.sin(t/5)*2;
    let voltage = 7 + Math.sin(t/4)*0.3;
    let pressure = 1000 + Math.sin(t/6)*5;

    document.getElementById("altitude").innerText = altitude.toFixed(1);
    document.getElementById("temp").innerText = temp.toFixed(1);
    document.getElementById("voltage").innerText = voltage.toFixed(2);
    document.getElementById("pressure").innerText = pressure.toFixed(1);

    document.getElementById("packet").innerText = t;

    pushData(altChart,altitude);
    pushData(tempChart,temp);
    pushData(voltChart,voltage);
    pushData(pressChart,pressure);

},1000);
