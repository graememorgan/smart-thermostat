Smart thermostat
================

A Flask-based thermometer logger and thermostat.  It:

- Logs the temperature, humidity, and pressure from sensors.
- Provides a web interface to view current and past data.
- Provides a web interface to set a seven day temperature schedule.
- Allows for manual timed overrides of temperature.

Some aspects are tied to other projects.  The actual thermostat control is a 433 MHz transmitter controlled by an ESP8266 running NodeMCU, which simulates the protocol used by my existing wireless thermostat.  The thermostat can be configured to automatically switch off when no one is home, which ties into a separate system which monitors the home WiFi for connections.

