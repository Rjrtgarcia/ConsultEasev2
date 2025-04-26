#ifndef MQTT_HANDLER_H
#define MQTT_HANDLER_H

#include <Arduino.h> // Include base Arduino definitions (for byte, boolean, etc.)
#include <WiFi.h>
#include <PubSubClient.h>

// Define the function signature for the MQTT message callback
// Parameters: topic, payload (byte array), length of payload
typedef void (*MQTT_CALLBACK_SIGNATURE)(char* topic, byte* payload, unsigned int length);

/**
 * @brief Sets the unique faculty ID for this unit.
 * This ID is used to construct faculty-specific MQTT topics.
 * @param id The faculty ID string.
 */
void set_faculty_id(const char* id);

/**
 * @brief Connects the ESP32 to the configured Wi-Fi network.
 * Blocks until connection is successful.
 */
void setup_wifi();

/**
 * @brief Configures the MQTT client with broker details and the message callback.
 * @param callback The function to be called when an MQTT message arrives.
 */
void setup_mqtt(MQTT_CALLBACK_SIGNATURE callback);

/**
 * @brief Attempts to connect/reconnect to the MQTT broker.
 * Handles subscription logic upon successful connection.
 * Should be called internally when a connection is lost.
 */
void reconnect_mqtt();

/**
 * @brief Maintains the MQTT connection and processes incoming messages.
 * Should be called repeatedly in the main Arduino loop.
 */
void mqtt_handler_loop();

/**
 * @brief Publishes a message to the specified MQTT topic.
 * @param topic The MQTT topic to publish to.
 * @param payload The message payload.
 * @param retained Whether the message should be retained by the broker. Defaults to false.
 */
void publish_message(const char* topic, const char* payload, boolean retained = false);


#endif // MQTT_HANDLER_H