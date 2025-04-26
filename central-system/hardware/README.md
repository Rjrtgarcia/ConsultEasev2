# Central System - Hardware Module

This module provides interfaces for interacting with hardware components connected to the Raspberry Pi (Central System).

## `rfid_reader.py`

Defines classes for handling RFID tag reading:
*   `RFIDReaderBase`: An abstract base class (currently unused directly).
*   `PN532Reader`: Implements reading from a PN532 RFID/NFC module connected via SPI. Includes basic debouncing logic. Requires `adafruit-circuitpython-pn532` and related libraries.
*   `SimulatedRFIDReader`: A software-only simulation used for testing the UI flow without actual hardware. Emits a signal when its `simulate_scan` method is called.
*   `RFIDReader`: A factory class that attempts to initialize the `PN532Reader` but falls back to the `SimulatedRFIDReader` if the hardware is not detected or libraries are missing.

## Current Usage Note

**Important:** The main application (`central-system/ui/auth_dialog.py`) has been updated to directly handle USB RFID readers that emulate a Keyboard HID device (typing UID + Enter) using the `keyPressEvent`.

Therefore, the `PN532Reader` and the `RFIDReader` factory class within `rfid_reader.py` are **not currently used** by the primary RFID reading mechanism in the `AuthDialog`.

The `SimulatedRFIDReader` class *is* still used by the simulation button within the `AuthDialog` for testing purposes.

The `PN532Reader` code is retained here as a reference or for potential future adaptation if the system needs to support non-HID readers (e.g., serial/UART/I2C based like the PN532) again.
The `AuthDialog` currently instantiates `SimulatedRFIDReader` directly for simplicity.

See the main project `README.md` for hardware connection details.