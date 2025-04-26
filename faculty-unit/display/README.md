# Faculty Unit - Display Module

This module manages the TFT LCD display connected to the ESP32 Faculty Unit.

## `display_manager.h` / `display_manager.cpp`

Defines and implements the `DisplayManager` static class:
*   Initializes the specific display hardware (ILI9341) using the `Adafruit_ILI9341` and `Adafruit_GFX` libraries.
*   Uses pin definitions (`TFT_CS`, `TFT_DC`, `TFT_RST`) and screen dimensions from `config.h`.
*   Provides static methods to:
    *   `setup_display()`: Initialize the screen.
    *   `clear_display()`: Clear the screen content.
    *   `show_status()`: Display the faculty's presence status (e.g., "Present") in a designated area.
    *   `show_request()`: Display incoming consultation request details (student ID, message) in a designated area.

The main `.ino` file calls these static methods to update the display based on BLE status and incoming MQTT requests.