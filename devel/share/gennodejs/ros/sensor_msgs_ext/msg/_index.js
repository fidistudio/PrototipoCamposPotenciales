
"use strict";

let gyroscope = require('./gyroscope.js');
let covariance = require('./covariance.js');
let time_reference = require('./time_reference.js');
let gnss_track = require('./gnss_track.js');
let axis_state = require('./axis_state.js');
let proximity = require('./proximity.js');
let magnetometer = require('./magnetometer.js');
let accelerometer = require('./accelerometer.js');
let gnss_position = require('./gnss_position.js');
let gnss_fix = require('./gnss_fix.js');
let analog_voltage = require('./analog_voltage.js');
let temperature = require('./temperature.js');

module.exports = {
  gyroscope: gyroscope,
  covariance: covariance,
  time_reference: time_reference,
  gnss_track: gnss_track,
  axis_state: axis_state,
  proximity: proximity,
  magnetometer: magnetometer,
  accelerometer: accelerometer,
  gnss_position: gnss_position,
  gnss_fix: gnss_fix,
  analog_voltage: analog_voltage,
  temperature: temperature,
};
