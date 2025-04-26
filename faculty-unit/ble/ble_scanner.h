#ifndef BLE_SCANNER_H
#define BLE_SCANNER_H

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "faculty-unit/config/config.h" // Include config for constants

/**
 * @brief Manages BLE scanning to detect the presence of a specific faculty beacon.
 */
class BLEScanner {
public:
    /**
     * @brief Constructor. Initializes targetAddress from config.
     */
    BLEScanner();

    /**
     * @brief Initializes the BLE stack and scanner object.
     */
    void setup_ble();

    /**
     * @brief Performs a BLE scan for the configured duration.
     *        Updates last_seen_ms if the target beacon is found.
     * @return true if the scan was initiated successfully, false otherwise.
     */
    bool scan();

    /**
     * @brief Checks if the target beacon has been seen within the configured timeout.
     * @return true if the beacon is considered present, false otherwise.
     */
    bool is_present();

private:
    unsigned long last_seen_ms; ///< Timestamp (millis) when the target beacon was last detected.
    BLEScan* pBLEScan;          ///< Pointer to the ESP32 BLE scan object.
    BLEAddress targetAddress;   ///< The MAC address of the target faculty beacon.
    // Optional: Callback class if using asynchronous scanning
    // class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
    //     void onResult(BLEAdvertisedDevice advertisedDevice) override;
    // };
};

#endif // BLE_SCANNER_H