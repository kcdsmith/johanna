'use strict';

exports.handler = (event, context, callback) => {
    var http = require("http");

    http.get('http://ifconfig.co', (res) => {
        res.setEncoding('utf8');
        let rawData = '';
        res.on('data', (chunk) => rawData += chunk);
        res.on('end', () => {
        console.log(rawData);
        });
    });
};
