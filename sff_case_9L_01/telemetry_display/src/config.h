#ifndef CONFIG_H
#define CONFIG_H

// ==============================================================================
// --- USER CONFIGURATION PARAMETERS ---
// ==============================================================================

// --- Display Settings ---
const bool isLandscape = false;
const int bootBrightness = 30;       // Brightness (0-255) when PC is off
const int standbyBrightness = 30;    // Brightness (0-255) after offline timeout expires

// --- Serial Communications ---
const long serialBaudRate = 115200;

// --- Timing & Thresholds ---
const unsigned long offlineTimeoutMs = 8000; // Milliseconds before reverting to Pip-Boy
const unsigned long sensorPollMs = 5000;     // Milliseconds between AHT20/BMP280 reads
const int ledThreshold = 3000;               // Optocoupler analog trigger threshold

// --- Hardware Pinouts ---
const int hddLedPin = 4;
const int pwrLedPin = 5;
const int i2cSdaPin = 0;
const int i2cSclPin = 1;

#endif