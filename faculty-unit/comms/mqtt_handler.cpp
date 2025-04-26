#include "mqtt_handler.h"
#include "config.h"
#include <WiFi.h> // Needed for WiFi.macAddress()
#include <string.h> // For strncpy
#include <ArduinoJson.h> // For JSON parsing
#include "display_manager.h" // For calling display functions

// Global WiFi and MQTT client instances
WiFiClient espClient;
PubSubClient client(espClient);

// Variable to store the faculty ID
char facultyId[32] = ""; // Adjust size as needed

// Variable to store the MQTT callback function pointer
MQTT_CALLBACK_SIGNATURE mqttCallback = NULL;

// Buffer for constructing MQTT topics
char topicBuffer[100]; // Adjust size as needed

/**
 * @brief Generates a unique MQTT client ID based on the ESP32's MAC address.
 * @return A String containing the unique client ID.
 */
String generateClientId() {
    String mac = WiFi.macAddress();
    mac.replace(":", ""); // Remove colons from MAC address
    return String(MQTT_CLIENT_ID_BASE) + mac;
}

/**
 * @brief Internal callback function registered with the PubSubClient library.
 *        Handles incoming MQTT messages, specifically parsing consultation requests
 *        and forwarding other messages to the user-provided callback.
 * @param topic The topic the message arrived on.
 * @param payload The message payload as a byte array.
 * @param length The length of the payload.
 */
void internalMqttCallback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");
    // Print payload
    for (int i = 0; i < length; i++) {
        Serial.print((char)payload[i]);
    }
    Serial.println();

    // Check if the message is for the general consultation request topic.
    // This topic is handled directly by the handler to update the display.
    if (strcmp(topic, MQTT_REQUEST_TOPIC) == 0) {
        // --- Handle Consultation Request ---
        Serial.println("Received new consultation request.");

        // Allocate a StaticJsonDocument.
        // Adjust size if necessary based on expected payload size.
        StaticJsonDocument<256> doc; // Increased size slightly for safety

        // Deserialize the JSON document
        DeserializationError error = deserializeJson(doc, payload, length);

        // Test if parsing succeeded.
        if (error) {
            Serial.print(F("deserializeJson() failed: "));
            Serial.println(error.f_str());
            return; // Exit if JSON is invalid
        }

        // Extract values
        const char* student_id = doc["student_id"];
        const char* request_text = doc["request_text"];
        // const char* request_id = doc["request_id"]; // Optional: if needed later for ACKs

        // Basic validation
        if (student_id == nullptr || request_text == nullptr) {
            Serial.println(F("Missing 'student_id' or 'request_text' in JSON payload."));
            return; // Exit if required fields are missing
        }

        Serial.print("Student ID: ");
        Serial.println(student_id);
        Serial.print("Request Text: ");
        Serial.println(request_text);

        // Call the static display manager function to show the request
        DisplayManager::show_request(student_id, request_text);

    } else {
        // --- Handle other topics via user callback ---
        // Call the user-provided callback if it's set and the topic is not the request topic
        if (mqttCallback != NULL) {
            Serial.println("Passing message to user callback.");
            mqttCallback(topic, payload, length);
        }
    }
}

/**
 * @brief Sets the unique faculty ID for this unit.
 *        This ID is used to construct faculty-specific MQTT topics.
 * @param id The faculty ID string (should be null-terminated).
 */
void set_faculty_id(const char* id) {
    strncpy(facultyId, id, sizeof(facultyId) - 1);
    facultyId[sizeof(facultyId) - 1] = '\0'; // Ensure null termination
    Serial.print("Faculty ID set to: ");
    Serial.println(facultyId);
}

/**
 * @brief Connects the ESP32 to the configured Wi-Fi network using credentials
 *        from config.h. Blocks until connection is successful.
 */
void setup_wifi() {
    delay(10); // Short delay before starting WiFi
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(WIFI_SSID);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("");
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
}

/**
 * @brief Configures the MQTT client with broker details from config.h
 *        and sets the message callback function.
 * @param callback The function pointer to the user's callback for non-request messages.
 */
void setup_mqtt(MQTT_CALLBACK_SIGNATURE callback) {
    mqttCallback = callback; // Store the user's callback function
    client.setServer(MQTT_BROKER, MQTT_PORT); // Set broker address and port
    client.setCallback(internalMqttCallback); // Register the internal callback wrapper
    Serial.println("MQTT Server and Callback configured.");
}

/**
 * @brief Attempts to connect to the MQTT broker. If connection fails,
 *        it waits for MQTT_RECONNECT_DELAY and tries again.
 *        Subscribes to the necessary topics upon successful connection.
 */
void reconnect_mqtt() {
    // Loop until we're reconnected
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        String clientId = generateClientId();
        Serial.print(" (Client ID: ");
        Serial.print(clientId);
        Serial.print(")");

        // Attempt to connect
        if (client.connect(clientId.c_str())) {
            Serial.println(" connected");

            // Subscribe to general request topic
            if (client.subscribe(MQTT_REQUEST_TOPIC)) {
                Serial.print("Subscribed to: ");
                Serial.println(MQTT_REQUEST_TOPIC);
            } else {
                Serial.print("Failed to subscribe to: ");
                Serial.println(MQTT_REQUEST_TOPIC);
            }

            // Add subscriptions to faculty-specific topics if needed
            // Example: Subscribe to a topic specific to this faculty unit
            // snprintf(topicBuffer, sizeof(topicBuffer), "consultease/faculty/%s/commands", facultyId);
            // if (client.subscribe(topicBuffer)) {
            //     Serial.print("Subscribed to: ");
            //     Serial.println(topicBuffer);
            // } else {
            //     Serial.print("Failed to subscribe to: ");
            //     Serial.println(topicBuffer);
            // }

        } else {
            Serial.print(" failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            // Wait 5 seconds before retrying
            delay(MQTT_RECONNECT_DELAY);
        }
    }
}

/**
 * @brief Maintains the MQTT connection and processes incoming/outgoing messages.
 *        Checks connection status and attempts reconnection if necessary.
 *        Calls the underlying PubSubClient loop function.
 *        Should be called repeatedly in the main Arduino loop.
 */
void mqtt_handler_loop() {
    if (!client.connected()) {
        reconnect_mqtt(); // Attempt to reconnect if disconnected
    }
    client.loop(); // Allow the MQTT client to process incoming messages and maintain connection
}

/**
 * @brief Publishes a message to the specified MQTT topic if connected.
 * @param topic The MQTT topic string.
 * @param payload The message payload string.
 * @param retained Boolean flag indicating if the message should be retained.
 */
void publish_message(const char* topic, const char* payload, boolean retained) {
    if (client.connected()) {
        Serial.print("Publishing to [");
        Serial.print(topic);
        Serial.print("]: ");
        Serial.println(payload);
        if (!client.publish(topic, payload, retained)) {
             Serial.println("MQTT Publish failed!");
        }
    } else {
        Serial.println("MQTT Client not connected. Cannot publish.");
    }
}