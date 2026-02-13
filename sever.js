const express = require('express');
const { SerialPort } = require('serialport');
const { ReadlineParser } = require('@serialport/parser-readline');
const WebSocket = require('ws');

const app = express();
const server = app.listen(3000);

app.use(express.static(__dirname));

const wss = new WebSocket.Server({ server });

const port = new SerialPort({
    path: 'COM3',   // เปลี่ยนตามเครื่องคุณ
    baudRate: 9600
});

const parser = port.pipe(new ReadlineParser({ delimiter: '\n' }));

parser.on('data', (data) => {
    wss.clients.forEach(client => {
        client.send(data);
    });
});
