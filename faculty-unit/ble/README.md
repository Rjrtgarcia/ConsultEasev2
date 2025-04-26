# Faculty Unit - BLE Module

This module handles Bluetooth Low Energy (BLE) scanning on the ESP32 Faculty Unit to detect the presence of a specific faculty member's beacon.

## `ble_scanner.h` / `ble_scanner.cpp`

Defines and implements the `BLEScanner` class:
*   Initializes the ESP32's BLE capabilities.
*   Configures and performs periodic BLE scans based on settings in `config.h`.
*   Checks scan results for the specific `TARGET_BLE_ADDRESS` defined in `config.h`.
*   Provides an `is_present()` method that returns `true` if the target beacon has been seen within the `PRESENCE_TIMEOUT_MS` (also defined in `config.h`).
*   Includes handling for `millis()` rollover.

The main `.ino` file uses this class to determine the faculty's presence status, which is then published via MQTT and displayed locally.