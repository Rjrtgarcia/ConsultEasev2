# ConsultEase - Faculty Consultation Queue System

## Project Overview

ConsultEase is a system designed to streamline the process for students seeking consultations with faculty members. It consists of two main components:

1.  **Central System (Raspberry Pi):** A touch-screen interface where students can select a faculty member, view their availability (indicated by BLE presence), and submit consultation requests using simulated RFID authentication. It also provides an administrative panel for managing faculty information.
2.  **Faculty Unit (ESP32):** A device located with the faculty member, displaying incoming consultation requests on a TFT screen and detecting the faculty member's presence via a BLE beacon.

The system uses MQTT for communication between the Central System and Faculty Units and Firebase Firestore as the backend database.

## Architecture

The system follows a distributed architecture:

*   **Frontend (Central System):** PyQt6 application running on a Raspberry Pi with a touchscreen. Handles user interaction, RFID reading, and communication initiation.
*   **Backend:** Firebase Firestore stores faculty data and potentially request logs (though current implementation focuses on real-time display).
*   **Communication:** MQTT broker facilitates real-time messaging between the Central System and Faculty Units.
*   **Faculty Presence:** BLE beacon carried by faculty is detected by the ESP32 Faculty Unit to update availability status.

For a more detailed description, see [documentation/ARCHITECTURE.md](documentation/ARCHITECTURE.md).

## Hardware Requirements

*   **Central System:**
    *   Raspberry Pi (Model 3B+ or newer recommended)
    *   Official Raspberry Pi 7" Touchscreen Display (or compatible)
    *   USB RFID Reader (13.56MHz, HID Keyboard Emulation type)
    *   RFID Cards/Tags (13.56MHz, compatible with reader)
*   **Faculty Unit (per faculty member):**
    *   ESP32 Development Board (e.g., ESP32-WROOM-32)
    *   ILI9341 TFT LCD Display (SPI interface, typically 2.4" - 3.2")
    *   BLE Beacon (e.g., an Eddystone or iBeacon compatible device)

## Software Dependencies

### Central System (Python)

*   Python 3.7+
*   Dependencies listed in `requirements.txt`. Install using:
    ```bash
    pip install -r requirements.txt
    ```
    Key libraries include:
    *   `firebase-admin`: For Firebase backend interaction.
    *   `PyQt6`: For the graphical user interface.
    *   `paho-mqtt`: For MQTT communication.
    *   *(Note: `adafruit-circuitpython-pn532` and `pyserial` might still be listed in requirements.txt but are not used for the primary HID RFID reader functionality)*

### Faculty Unit (Arduino/C++)

*   Arduino IDE or PlatformIO
*   ESP32 Board Support Package
*   **Libraries:** (Install via Arduino Library Manager or PlatformIO `lib_deps`)
    *   `Adafruit GFX Library`
    *   `Adafruit_ILI9341` (or appropriate driver for your specific TFT)
    *   `PubSubClient`: For MQTT communication.
    *   `ArduinoJson`: For parsing/creating JSON payloads.
    *   ESP32 BLE Libraries (built-in, ensure correct configuration for scanning)

## Firebase Setup

1.  **Create Firebase Project:** Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.
2.  **Enable Firestore:** In your Firebase project, navigate to Firestore Database and create a database in Native mode. Choose your location.
3.  **Create Service Account:**
    *   Go to Project Settings -> Service accounts.
    *   Click "Generate new private key" and save the downloaded JSON file.
4.  **Place Key:** Rename the downloaded JSON file to `firebase-service-account.json` and place it in the `central-system/` directory.
    *   **Important:** This file contains sensitive credentials. Ensure `firebase-service-account.json` is listed in your `.gitignore` file (it should be by default in this project) to prevent accidentally committing it to version control.
5.  **Database Structure:** The system expects a `faculty` collection in Firestore. Each document in this collection represents a faculty member and should contain fields like `name`, `department`, `facultyId` (unique identifier), `status` (e.g., "Available", "Unavailable"), `rfid_uid` (optional, if linking specific RFID tags), `ble_address` (MAC address of their BLE beacon), and `mqtt_topic` (unique topic for their unit). The Admin Panel helps manage this.

## Installation

### Central System (Raspberry Pi)

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd ConsultEase
    ```
2.  **Install Dependencies:**
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip git # Basic requirements
    pip install -r requirements.txt
    ```
3.  **Place Firebase Key:** Ensure `firebase-service-account.json` is in the `central-system/` directory (see Firebase Setup).
4.  **Configure Hardware:** Connect the USB RFID Reader. As it functions as a Keyboard HID device, no specific drivers are typically needed on Raspberry Pi OS. The system should recognize it automatically. Connect the touchscreen.
5.  **Install On-Screen Keyboard (Recommended for Kiosk):**
    ```bash
    sudo apt install squeekboard
    ```

### Faculty Unit (ESP32)

1.  **Setup IDE:** Install Arduino IDE or PlatformIO with ESP32 support.
2.  **Install Libraries:** Install the required libraries mentioned in Software Dependencies.
3.  **Configure `config.h`:** Open `faculty-unit/config/config.h` and update the following:
    *   `WIFI_SSID` and `WIFI_PASSWORD`: Your Wi-Fi network credentials.
    *   `MQTT_BROKER`: The IP address or hostname of your MQTT broker (e.g., the IP address of the Raspberry Pi if running a local broker, or a cloud broker address).
    *   `MQTT_PORT`: The port for the MQTT broker (usually 1883).
    *   `FACULTY_ID`: A unique identifier for this specific faculty unit (e.g., "prof_smith"). This should match the `facultyId` in the Firestore database.
    *   `FACULTY_BLE_ADDRESS`: The MAC address of the BLE beacon associated with this faculty member (e.g., "AA:BB:CC:11:22:33").
    *   `TFT_CS`, `TFT_DC`, `TFT_RST`: Pin connections for your specific TFT display. Adjust if different from defaults.
    *   Other pins as needed (e.g., `LED_PIN`).
4.  **Flash ESP32:** Connect the ESP32 to your computer, select the correct board and port in your IDE, and upload the `faculty-unit/faculty_unit.ino` sketch.

## Configuration

*   **Central System:**
    *   Firebase credentials (`central-system/firebase-service-account.json`).
    *   MQTT Broker details are configured within `central-system/comms/mqtt_client.py` (consider moving to a config file or environment variables for better practice).
    *   RFID reader (USB HID) requires no specific software configuration; it's handled directly in the UI code (`central-system/ui/auth_dialog.py`).
*   **Faculty Unit:**
    *   All primary configuration is done in `faculty-unit/config/config.h` as described in the Installation section.

## Running the System

1.  **Start MQTT Broker:** Ensure your MQTT broker is running (e.g., Mosquitto on the Raspberry Pi or a cloud service).
2.  **Run Central System:**
    *   Navigate to the project root directory on the Raspberry Pi.
    *   Execute the main application:
        ```bash
        python central-system/main.py
        ```
    *   For Kiosk mode (optional, requires setup): Configure the Pi to automatically launch the script on boot, potentially hiding the desktop environment. Ensure `squeekboard` is configured if needed for text input (like in the Admin Panel).
3.  **Power Faculty Unit:** Connect the flashed ESP32 Faculty Unit to power. It should automatically connect to Wi-Fi, MQTT, and start displaying information and scanning for its assigned BLE beacon.

## Usage Instructions

1.  **Student Verification:**
    *   Approach the Central System (Raspberry Pi touchscreen).
    *   When the "Student Verification" dialog appears:
        *   **Using RFID Reader:** Scan your 13.56MHz RFID card/tag. The USB HID reader will type the card's UID and simulate pressing Enter. The dialog listens for this keyboard input.
        *   **Using Simulation:** Alternatively, type a known student RFID UID into the simulation input field on the dialog and click the "Simulate Scan" button.
    *   *(Note: The system currently verifies the UID against faculty data for simplicity, not a separate student database).*
2.  **View Faculty & Submit Request:**
    *   The main screen displays a list of faculty members fetched from Firebase.
    *   Faculty status ("Available", "Unavailable") is updated based on BLE beacon detection by their respective Faculty Unit and communicated via MQTT.
    *   Select an available faculty member.
    *   Click a "Submit Request" or similar button.
    *   A confirmation message appears, and the request is sent via MQTT to the selected faculty member's unit.
3.  **Faculty Unit Operation:**
    *   The Faculty Unit's TFT display shows the faculty member's name/ID and current status.
    *   When a student submits a request via the Central System, the request details (e.g., "Student Request Pending") appear on the TFT display.
    *   The display updates automatically based on BLE presence detection and incoming MQTT messages.

## Admin Functionality Guide

1.  **Access:** Access to the Admin Panel might be via a specific button or sequence on the main UI (e.g., an "Admin" button). *Note: Current implementation lacks robust security; this should be added in a production environment.*
2.  **Functionality:** The Admin Panel (`central-system/ui/admin_panel.py`) allows authorized users to:
    *   **View:** See a list of all faculty members registered in the Firebase database.
    *   **Add:** Add a new faculty member by providing their Name, Department, Faculty ID, BLE Address, and optionally RFID UID.
    *   **Edit:** Modify the details of an existing faculty member.
    *   **Delete:** Remove a faculty member from the system.
3.  **Data Synchronization:** All changes made in the Admin Panel are directly reflected in the Firebase Firestore database.

## Troubleshooting Guide

*   **Central System UI Doesn't Start:**
    *   Check Python and PyQt6 installation.
    *   Verify `requirements.txt` dependencies are installed.
    *   Look for error messages in the terminal output.
    *   Ensure the display server (X11) is running.
*   **Cannot Connect to Firebase:**
    *   Verify `firebase-service-account.json` is present in `central-system/` and is valid.
    *   Check the Raspberry Pi's internet connection.
    *   Ensure Firestore database is created and rules allow access (default rules are often permissive initially).
*   **MQTT Connection Errors (Central System or Faculty Unit):**
    *   Ensure the MQTT broker is running and accessible from both devices.
    *   Verify the broker address and port are correctly configured in `central-system/comms/mqtt_client.py` and `faculty-unit/config/config.h`.
    *   Check device Wi-Fi connections.
    *   Look for firewall rules blocking MQTT ports (default 1883).
*   **Faculty Unit Display Not Working:**
    *   Double-check `TFT_CS`, `TFT_DC`, `TFT_RST` pin definitions in `config.h` match your wiring.
    *   Ensure correct TFT driver library (`Adafruit_ILI9341` or equivalent) is installed and used.
    *   Verify power supply to the ESP32 and TFT.
*   **Faculty Status Not Updating / BLE Not Detected:**
    *   Verify the `FACULTY_BLE_ADDRESS` in `config.h` exactly matches the faculty member's beacon MAC address.
    *   Ensure the BLE beacon is powered on and within range of the ESP32.
    *   Check the ESP32's serial monitor output for BLE scanning messages or errors.
    *   Confirm MQTT messages for status updates are being sent/received correctly.
*   **USB RFID Reader Not Detected/Working:**
    *   **Reader Not Detected:** Check the USB connection. Ensure the reader is powered and recognized by the OS (it should appear as a keyboard-like device). Verify it's a HID Keyboard Emulation type.
    *   **Scanned ID Not Processed:** Ensure the reader is configured to send an "Enter" key press after transmitting the UID. Check that the `AuthDialog` window has focus when scanning. Verify the `keyPressEvent` logic in `auth_dialog.py` is correctly capturing the input sequence.
    *   **Incorrect ID:** Confirm the reader outputs the expected UID format.

## Hardware Setup (Textual Description)

*(Note: Specific GPIO pins for the Faculty Unit may vary based on ESP32 model and user configuration. These are typical examples.)*

### Central System (Raspberry Pi)

*   **USB RFID Reader:** Connect to any available USB port on the Raspberry Pi.
*   **Touchscreen:** Typically connects via DSI ribbon cable and specific GPIOs for power/touch.

### Faculty Unit (ESP32 + ILI9341 TFT Example)

*   ESP32 3.3V -> TFT VCC
*   ESP32 GND -> TFT GND
*   ESP32 Pin defined in `config.h` (e.g., GPIO 5) -> TFT CS (Chip Select)
*   ESP32 Pin defined in `config.h` (e.g., GPIO 4) -> TFT RST (Reset)
*   ESP32 Pin defined in `config.h` (e.g., GPIO 2) -> TFT DC (Data/Command)
*   ESP32 Pin VSPI MOSI (e.g., GPIO 23) -> TFT SDI/MOSI (Serial Data In)
*   ESP32 Pin VSPI SCK (e.g., GPIO 18) -> TFT SCK/CLK (Serial Clock)
*   ESP32 3.3V -> TFT LED (Backlight - may need a resistor or dedicated pin control)
*   *(MISO (GPIO 19) is often not needed for display-only)*

---
*This README provides a comprehensive guide to setting up, configuring, and using the ConsultEase system.*