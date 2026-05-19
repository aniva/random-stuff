#ifndef CONFIG_H
#define CONFIG_H

// ==============================================================================
// --- USER CONFIGURATION PARAMETERS ---
// ==============================================================================

// --- Display Settings ---
const bool isLandscape = false;
const int bootBrightness = 3;      // Brightness (0-255) when PC is off
const int standbyBrightness = 3;    // Aligns offline brightness with night-mode daemon target

// --- Serial Communications ---
const long serialBaudRate = 115200;

// --- Timing & Thresholds ---
const unsigned long offlineTimeoutMs = 8000; // Milliseconds before reverting to Pip-Boy
const unsigned long sensorPollMs = 5000;     // Milliseconds between ambient reads
const int ledThreshold = 3000;               // Optocoupler analog trigger threshold

// --- Hardware Pinouts ---
const int hddLedPin = 4;
const int pwrLedPin = 5;

// Front Ambient Sensor (AHT20 Primary)
const int i2c0SdaPin = 0;
const int i2c0SclPin = 1;

// Rear Ambient Sensor (AHT20 Secondary)
const int i2c1SdaPin = 2;
const int i2c1SclPin = 3;

#endif