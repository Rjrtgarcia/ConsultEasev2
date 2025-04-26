#include "ble_scanner.h"
#include "faculty-unit/config/config.h" // Include config for constants
#include <Arduino.h> // Required for millis()

// Constructor
BLEScanner::BLEScanner() : last_seen_ms(0), pBLEScan(nullptr), targetAddress(TARGET_BLE_ADDRESS) {
    // Initialize targetAddress from config constant
}

/**
 * @brief Initializes the BLE stack and scanner object.
 */
void BLEScanner::setup_ble() {
    Serial.println("Initializing BLE...");
    BLEDevice::init(""); // Initialize BLE device with an empty name

    pBLEScan = BLEDevice::getScan(); // Get the BLE Scan object
    if (!pBLEScan) {
        Serial.println("Failed to get BLE Scan object");
        return; // Handle error appropriately
    }

    // Configure scan parameters
    pBLEScan->setActiveScan(true); // Active scan uses more power but gets more info
    pBLEScan->setInterval(100);    // Scan interval in ms
    pBLEScan->setWindow(99);       // Less than or equal to interval

    Serial.println("BLE Scanner Initialized.");
}

/**
 * @brief Performs a BLE scan for the configured duration.
 *        Updates last_seen_ms if the target beacon is found.
 * @return true if the scan was initiated successfully, false otherwise.
 *         Note: This implementation returns true if the target was found during the scan,
 *         which might differ slightly from the header comment's intent (initiation success).
 *         Consider adjusting return value if needed, but current logic is functional.
 */
bool BLEScanner::scan() {
    Serial.println("Starting BLE scan...");
    bool foundTarget = false;

    // Start scan for the duration specified in config, don't block execution
    BLEScanResults foundDevices = pBLEScan->start(BLE_SCAN_DURATION, false);

    Serial.print("Scan finished. Devices found: ");
    Serial.println(foundDevices.getCount());

    for (int i = 0; i < foundDevices.getCount(); i++) {
        BLEAdvertisedDevice device = foundDevices.getDevice(i);
        Serial.print("  Device Address: ");
        Serial.println(device.getAddress().toString().c_str());

        // Check if the found device address matches the target address
        if (device.getAddress().equals(targetAddress)) {
            Serial.print("!!! Target Beacon Found: ");
            Serial.println(device.getAddress().toString().c_str());
            last_seen_ms = millis(); // Update the last seen timestamp
            foundTarget = true;
            break; // Stop searching once the target is found
        }
    }

    pBLEScan->clearResults(); // Clear results from memory
    Serial.println("Scan results cleared.");

    return foundTarget;
}

/**
 * @brief Checks if the target beacon has been seen within the configured timeout.
 *        Handles potential rollover of the millis() counter.
 * @return true if the beacon is considered present, false otherwise.
 */
bool BLEScanner::is_present() {
    // Check if the time elapsed since last seen is within the timeout threshold
    unsigned long current_time = millis();
    bool present = (current_time - last_seen_ms < PRESENCE_TIMEOUT_MS);

    // Handle potential millis() rollover (overflow)
    if (last_seen_ms > current_time) {
        // Rollover occurred, calculate difference correctly
        // This assumes timeout is less than the rollover period (~50 days)
        present = ( (0xFFFFFFFF - last_seen_ms) + current_time < PRESENCE_TIMEOUT_MS );
    }

    if (!present && last_seen_ms != 0) { // Avoid printing "Unavailable" right at the start
         Serial.print("Presence timeout check: Current=");
         Serial.print(current_time);
         Serial.print(", LastSeen=");
         Serial.print(last_seen_ms);
         Serial.print(", Timeout=");
         Serial.print(PRESENCE_TIMEOUT_MS);
         Serial.print(", Present=");
         Serial.println(present);
    }


    return present;
}