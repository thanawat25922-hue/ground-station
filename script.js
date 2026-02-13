let pkt = 0;

setInterval(() => {

    pkt++;

    document.getElementById("pkt").innerText = pkt;
    document.getElementById("temp").innerText = (24 + Math.random()*2).toFixed(1);
    document.getElementById("alt").innerText = (180 + Math.random()*5).toFixed(0);
    document.getElementById("hum").innerText = (40 + Math.random()*10).toFixed(0);
    document.getElementById("rssi").innerText = -60 - Math.random()*10;

}, 1000);
