#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// MQTT Configuration
#define MQTT_BROKER "YOUR_MQTT_BROKER_IP" // Replace with your MQTT broker IP or hostname
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID_BASE "faculty_unit_" // Base for client ID, will be appended with chip ID
#define FACULTY_ID "prof_smith"             // Unique ID for this faculty unit

// MQTT Topics (Based on documentation/ARCHITECTURE.md)
// Template for faculty-specific status topic. %s will be replaced by faculty ID.
#define MQTT_STATUS_TOPIC_TEMPLATE "consultease/faculty/%s/status"
// Topic for new consultation requests (faculty units subscribe to this)
#define MQTT_REQUEST_TOPIC "consultease/requests/new"
// Topic for faculty availability updates (faculty units publish to this)
#define MQTT_AVAILABILITY_TOPIC_TEMPLATE "consultease/faculty/%s/availability"
// Topic for acknowledging requests (faculty units publish to this)
#define MQTT_ACKNOWLEDGE_TOPIC_TEMPLATE "consultease/requests/%s/acknowledge" // %s is request ID

// BLE Configuration
#define TARGET_BLE_ADDRESS "AA:BB:CC:DD:EE:FF" // Replace with the actual faculty beacon MAC address
#define BLE_SCAN_DURATION 5                   // Scan duration in seconds
#define PRESENCE_TIMEOUT_MS 15000             // Timeout in milliseconds for presence detection

// Display Configuration (2.4" SPI TFT ILI9341)
#define SCREEN_WIDTH 240 // TFT display width, in pixels
#define SCREEN_HEIGHT 320 // TFT display height, in pixels

// Define the SPI pins for the TFT display
// ** IMPORTANT: Update these pins to match your ESP32 wiring! **
#define TFT_CS    5  // Chip Select pin (Example: GPIO5)
#define TFT_DC    4  // Data/Command pin (Example: GPIO4)
#define TFT_RST   2  // Reset pin (Example: GPIO2, use -1 if not connected)
// Standard SPI pins (MOSI, MISO, SCK) are usually handled by the library/hardware SPI

// Other constants
#define SERIAL_BAUD_RATE 115200
#define MQTT_RECONNECT_DELAY 5000 // Delay in ms before attempting MQTT reconnect

#endif // CONFIG_H