/*
 * ConsultEase Faculty Unit
 * ESP32 Implementation
 */

// #include <WiFi.h> // Now included via mqtt_handler.h
// #include <PubSubClient.h> // Now included via mqtt_handler.h
#include <ArduinoJson.h> // Keep for JSON handling in callbacks
#include "config.h"       // Include project configuration
#include "comms/mqtt_handler.h" // Include our MQTT handler
#include "ble/ble_scanner.h"    // Include our BLE Scanner
#include "display/display_manager.h" // Include our Display Manager
#include <Firebase_ESP_Client.h>

// Include Firebase auth helper
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

// WiFi credentials (Now defined in config.h)
// const char* ssid = "YOUR_WIFI_SSID";
// const char* password = "YOUR_WIFI_PASSWORD";

// MQTT settings (Now defined in config.h or handled by mqtt_handler)
// const char* mqtt_server = "YOUR_MQTT_SERVER";
// const int mqtt_port = 1883;
// const char* mqtt_client_id = "faculty_unit_";  // Will append MAC address
// const char* mqtt_topic_prefix = "consultease/faculty/"; // Use templates from config.h

// Firebase settings
#define API_KEY "YOUR_FIREBASE_API_KEY"
#define DATABASE_URL "https://consultease-prod.firebaseio.com"

// Faculty settings
const char* faculty_id = "faculty1";  // This should be configurable
const char* faculty_name = "John Doe";
const char* faculty_department = "Computer Science";

// Display settings (Now defined in config.h and managed by DisplayManager)
// const int DISPLAY_WIDTH = 128;
// const int DISPLAY_HEIGHT = 64;

// Status LED pins
const int LED_AVAILABLE = 12;
const int LED_BUSY = 14;
const int LED_AWAY = 27;

// Button pins
const int BTN_AVAILABLE = 32;
const int BTN_BUSY = 33;
const int BTN_AWAY = 25;

// Global objects
// WiFiClient espClient; // Now managed by mqtt_handler.cpp
// PubSubClient mqtt(espClient); // Now managed by mqtt_handler.cpp
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;
BLEScanner bleScanner; // Instance of our BLE Scanner
// DisplayManager displayManager; // Instance removed - using static methods

// Status variables
String currentStatus = "offline"; // Tracks the *manual* status set by buttons or remote MQTT command (available, busy, away)
unsigned long lastStatusUpdate = 0; // Timestamp for general updates (less used now)
bool firebaseConnected = false;
// bool mqttConnected = false; // Connection status managed internally by mqtt_handler
String last_published_status = "Unknown"; // Tracks the last *BLE presence* status published ("Present", "Unavailable")

// BLE Scanner - Replaced by BLEScanner class instance
// NimBLEScan* pBLEScan = nullptr;
// bool bleInitialized = false;

// Forward declarations
// void setupWiFi(); // Now handled by mqtt_handler
// void setupMQTT(); // Now handled by mqtt_handler
void setupFirebase();
// void setupBLE(); // Replaced by bleScanner.setup_ble()
// void setupDisplay(); // Now handled by displayManager.setup_display()
void setupLEDs();
void setupButtons();
// void reconnectMQTT(); // Now handled by mqtt_handler
void mqtt_message_callback(char* topic, byte* payload, unsigned int length); // Renamed callback
void updateStatus(String newStatus);
// void scanForBeacons(); // Replaced by bleScanner.scan() and bleScanner.is_present()
// void updateDisplay(); // Now handled by displayManager methods in loop()
void checkButtons();
void publishStatus();

void setup() {
  // Initialize serial
  Serial.begin(SERIAL_BAUD_RATE); // Use constant from config.h
  Serial.println("\nConsultEase Faculty Unit Starting...");

  // Setup hardware
  setupLEDs();
  setupButtons();
  // setupDisplay(); // Replaced by displayManager call below
  
  // Setup connectivity
  set_faculty_id(FACULTY_ID); // Use FACULTY_ID from config.h for the MQTT handler
  setup_wifi();               // Call MQTT handler's WiFi setup
  setup_mqtt(mqtt_message_callback); // Call MQTT handler's MQTT setup, pass callback
    setupFirebase();
    bleScanner.setup_ble(); // Initialize our BLE scanner

    // Initialize Display using static method
    if (!DisplayManager::setup_display()) {
        Serial.println("FATAL: Display setup failed. Halting.");
        while(1) { delay(1000); } // Stop execution
    }
  
    // Initial status update (for LEDs/MQTT, display handled separately in loop)
    updateStatus("available");
  
  Serial.println("Setup complete");
}

// Define BLE scan timing variables
unsigned long lastBleScanTime = 0;
// Scan slightly more often than the scan duration to avoid missing beacons
const unsigned long BLE_SCAN_INTERVAL_MS = (BLE_SCAN_DURATION * 1000) + 1000;

void loop() {
  // Check WiFi connection (Handled by mqtt_handler_loop now)
  // if (WiFi.status() != WL_CONNECTED) {
  //   Serial.println("WiFi connection lost. Reconnecting...");
  //   setup_wifi(); // Should call the handler's setup
  // }

  // MQTT connection and message processing is handled by the handler's loop function
  mqtt_handler_loop();

  // Check buttons for status changes
  checkButtons();

  // --- BLE Presence Check & MQTT Publish ---
  unsigned long currentMillis = millis();

  // Periodically trigger a BLE scan
  if (currentMillis - lastBleScanTime >= BLE_SCAN_INTERVAL_MS || lastBleScanTime == 0) { // Scan immediately on first loop
      Serial.println("Triggering BLE Scan...");
      bleScanner.scan(); // Perform the scan (non-blocking)
      lastBleScanTime = currentMillis;
      // Scan is triggered, is_present() below will use latest scan results or timeout logic
  }

  // Check current presence status (can be checked anytime)
  bool present = bleScanner.is_present();
  String current_status_string = present ? "Present" : "Unavailable";

  // Check if status has changed since last publish
  if (current_status_string != last_published_status) {
      Serial.print("Presence status changed to: ");
      Serial.println(current_status_string);

      // Construct the specific MQTT topic
      char topic_buffer[100]; // Ensure buffer is large enough
      snprintf(topic_buffer, sizeof(topic_buffer), MQTT_STATUS_TOPIC_TEMPLATE, FACULTY_ID);

      // Publish the new status as a retained message
      Serial.print("Publishing presence status to topic: ");
      Serial.println(topic_buffer);
      publish_message(topic_buffer, current_status_string.c_str(), true); // Publish "Present" or "Unavailable"

      // Update the tracking variable
      last_published_status = current_status_string;
  }

  // --- Display Update ---
  // The display primarily shows the faculty's *presence* based on BLE detection.
  // MQTT status updates reflect both BLE presence and manual button status on different topics/payloads.
  DisplayManager::show_status(current_status_string.c_str()); // Show "Present" or "Unavailable" based on BLE
  // DisplayManager::update_display(); // No longer needed for ILI9341

  // Remove old periodic display update logic
  // if (currentMillis - lastStatusUpdate > 5000) {
  //   updateDisplay(); // Old function call
  //   lastStatusUpdate = currentMillis;
  // }
  
  // Small delay to prevent CPU hogging
  delay(100);
}

// --- Removed old WiFi/MQTT setup and reconnect functions ---
// void setupWiFi() { ... }
// void setupMQTT() { ... }
// void reconnectMQTT() { ... }
// --- End Removed Functions ---


void setupFirebase() {
  Serial.println("Setting up Firebase...");
  
  // Configure Firebase
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  
  // Initialize Firebase
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  
  // Check connection
  if (Firebase.ready()) {
    Serial.println("Firebase connected");
    firebaseConnected = true;
    
    // Update faculty status in Firebase
    String path = "faculty/" + String(faculty_id) + "/status";
    Firebase.RTDB.setString(&fbdo, path.c_str(), currentStatus);
  } else {
    Serial.println("Firebase connection failed");
    firebaseConnected = false;
  }
}

// --- Removed old setupBLE() function ---

// --- Removed old setupDisplay() function, now handled by DisplayManager ---
// void setupDisplay() { ... }

void setupLEDs() {
  Serial.println("Setting up status LEDs...");
  
  pinMode(LED_AVAILABLE, OUTPUT);
  pinMode(LED_BUSY, OUTPUT);
  pinMode(LED_AWAY, OUTPUT);
  
  // All LEDs off initially
  digitalWrite(LED_AVAILABLE, LOW);
  digitalWrite(LED_BUSY, LOW);
  digitalWrite(LED_AWAY, LOW);
  
  Serial.println("LEDs initialized");
}

void setupButtons() {
  Serial.println("Setting up buttons...");
  
  pinMode(BTN_AVAILABLE, INPUT_PULLUP);
  pinMode(BTN_BUSY, INPUT_PULLUP);
  pinMode(BTN_AWAY, INPUT_PULLUP);
  
  Serial.println("Buttons initialized");
}

// Renamed function to match the signature passed to setup_mqtt
void mqtt_message_callback(char* topic, byte* payload, unsigned int length) {
  // The mqtt_handler.cpp internal callback already prints this
  // Serial.print("Message arrived [");
  // Serial.print(topic);
  Serial.print("] ");
  
  // Convert payload to string
  char message[length + 1];
  memcpy(message, payload, length);
  message[length] = '\0';
  Serial.println(message);
  
  // Parse JSON payload (Expected format: {"command": "...", "payload": ...})
  DynamicJsonDocument doc(1024); // Adjust size if needed for larger payloads
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Handle command
  String command = doc["command"].as<String>();
  
  if (command == "status_update") {
    // Publish current status
    publishStatus();
  } else if (command == "display_update") {
    // Update display with custom message
    String message = doc["message"].as<String>();
    // This would update the actual display
    Serial.print("Display update: ");
    Serial.println(message);
    // updateDisplay(); // Obsolete call removed
  } else if (command == "set_status") {
    // Set status remotely
    String newStatus = doc["status"].as<String>();
    updateStatus(newStatus);
  }
}

/**
 * @brief Updates the faculty's *manual* status based on button presses or remote commands.
 *        Updates LEDs, publishes the manual status via MQTT, and updates Firebase RTDB.
 * @param newStatus The new manual status ("available", "busy", "away").
 */
void updateStatus(String newStatus) {
  if (newStatus == currentStatus) {
    return;  // No change
  }
  
  Serial.print("Updating status from ");
  Serial.print(currentStatus);
  Serial.print(" to ");
  Serial.println(newStatus);
  
  currentStatus = newStatus;
  
  // Update LEDs
  digitalWrite(LED_AVAILABLE, currentStatus == "available" ? HIGH : LOW);
  digitalWrite(LED_BUSY, currentStatus == "busy" ? HIGH : LOW);
  digitalWrite(LED_AWAY, currentStatus == "away" ? HIGH : LOW);
  
  // Update display (Removed - Loop now handles display based on BLE status)
  // updateDisplay(); // Obsolete call removed

  // Publish to MQTT
  publishStatus();
  
  // Update Firebase
  if (firebaseConnected) {
    String path = "faculty/" + String(faculty_id) + "/status";
    Firebase.RTDB.setString(&fbdo, path.c_str(), currentStatus);
  }
}

// --- Removed old scanForBeacons() function ---

// --- Removed old updateDisplay() function, now handled by DisplayManager ---
// void updateDisplay() { ... }

void checkButtons() {
  // Check available button
  if (digitalRead(BTN_AVAILABLE) == LOW) {
    delay(50);  // Debounce
    if (digitalRead(BTN_AVAILABLE) == LOW) {
      updateStatus("available");
      while (digitalRead(BTN_AVAILABLE) == LOW) {
        delay(10);  // Wait for button release
      }
    }
  }
  
  // Check busy button
  if (digitalRead(BTN_BUSY) == LOW) {
    delay(50);  // Debounce
    if (digitalRead(BTN_BUSY) == LOW) {
      updateStatus("busy");
      while (digitalRead(BTN_BUSY) == LOW) {
        delay(10);  // Wait for button release
      }
    }
  }
  
  // Check away button
  if (digitalRead(BTN_AWAY) == LOW) {
    delay(50);  // Debounce
    if (digitalRead(BTN_AWAY) == LOW) {
      updateStatus("away");
      while (digitalRead(BTN_AWAY) == LOW) {
        delay(10);  // Wait for button release
      }
    }
  }
}

void publishStatus() {
  // Connection check is handled within publish_message
  // if (!mqttConnected) {
  //   return;
  // }

  // Construct topic using template from config.h
  char statusTopic[100]; // Make sure buffer is large enough
  snprintf(statusTopic, sizeof(statusTopic), MQTT_STATUS_TOPIC_TEMPLATE, faculty_id);

  DynamicJsonDocument doc(256);
  doc["status"] = currentStatus;
  doc["name"] = faculty_name;
  doc["department"] = faculty_department;
  doc["timestamp"] = millis();
  
  String statusPayload;
  serializeJson(doc, statusPayload);

  // Use the handler's publish function
  publish_message(statusTopic, statusPayload.c_str(), true);
}