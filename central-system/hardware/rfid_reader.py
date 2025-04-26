#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConsultEase Central System
RFID Reader Interface
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from PyQt6.QtCore import QObject, pyqtSignal

# Optional hardware imports - will be imported only if available
try:
    import board
    import busio
    import digitalio
    from adafruit_pn532.spi import PN532_SPI
    HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    HARDWARE_AVAILABLE = False

logger = logging.getLogger(__name__)

class RFIDReaderBase(ABC, QObject):
    """Base class for RFID readers"""
    
    # Signal emitted when a tag is detected
    tag_detected = pyqtSignal(str)
    
    @abstractmethod
    def start(self):
        """Start reading RFID tags"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop reading RFID tags"""
        pass
    
    @abstractmethod
    def is_available(self):
        """Check if the reader is available"""
        pass

class PN532Reader(RFIDReaderBase):
    """PN532 RFID reader implementation"""
    
    def __init__(self, spi_bus=0, cs_pin=5):
        super().__init__()
        self.spi_bus = spi_bus
        self.cs_pin = cs_pin
        self.pn532 = None
        self.running = False
        self.thread = None
        self._last_uid = None
        self._debounce_time = 1.5  # 1.5 seconds debounce
        self._last_read_time = 0
        
    def is_available(self):
        """Check if the PN532 reader is available"""
        if not HARDWARE_AVAILABLE:
            return False
        
        try:
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            cs = digitalio.DigitalInOut(getattr(board, f'D{self.cs_pin}'))
            self.pn532 = PN532_SPI(spi, cs, debug=False)
            ic, ver, rev, support = self.pn532.firmware_version
            logger.info(f"Found PN532 with firmware version: {ver}.{rev}")
            self.pn532.SAM_configuration()
            return True
        except Exception as e:
            logger.error(f"PN532 not available: {e}")
            return False
    
    def start(self):
        """Start reading RFID tags in a separate thread"""
        if self.running:
            return
        
        if not self.is_available():
            logger.error("Cannot start PN532 reader: hardware not available")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        logger.info("PN532 reader started")
    
    def stop(self):
        """Stop reading RFID tags"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.info("PN532 reader stopped")
    
    def _read_loop(self):
        """Continuously read RFID tags"""
        while self.running:
            try:
                # Check if a card is available to read
                uid = self.pn532.read_passive_target(timeout=0.5)
                
                # If a card is found...
                if uid:
                    current_time = time.time()
                    # ...and it's a new scan (not the same card within the debounce period)
                    if (uid != self._last_uid) or (current_time - self._last_read_time > self._debounce_time):
                        # Convert UID bytes to hex string
                        uid_string = ''.join([f'{i:02X}' for i in uid])
                        logger.info(f"Card detected with UID: {uid_string}")

                        # Update last read time and UID
                        self._last_read_time = current_time
                        self._last_uid = uid # Store raw UID for comparison

                        # Emit the signal with the UID
                        self.tag_detected.emit(uid_string)
                    
                # Small delay to prevent CPU hogging
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error reading RFID tag: {e}")
                time.sleep(1.0)  # Longer delay on error

class SimulatedRFIDReader(QObject): # Changed inheritance from RFIDReaderBase to QObject as per instructions
    """
    Simulated RFID reader for testing UI flows without hardware.
    Emits an rfid_scanned signal when simulate_scan is called.
    """
    rfid_scanned = pyqtSignal(str) # Renamed signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_reading = False
        logger.info("SimulatedRFIDReader initialized.")

    def start_reading(self):
        """'Starts' the simulated reader (enables scan simulation)."""
        self._is_reading = True
        logger.info("Simulated RFID reader started (ready for simulation).")
        # No timer needed for manual simulation via button

    def stop_reading(self):
        """'Stops' the simulated reader (disables scan simulation)."""
        self._is_reading = False
        logger.info("Simulated RFID reader stopped.")

    def simulate_scan(self, tag_id="SIM_12345"):
        """
        Simulates an RFID scan event.

        Args:
            tag_id (str): The RFID tag ID to simulate. Defaults to "SIM_12345".
        """
        if self._is_reading:
            logger.info(f"Simulating RFID scan with tag_id: {tag_id}")
            self.rfid_scanned.emit(tag_id)
        else:
            logger.warning("Simulate scan called while reader is stopped.")

# --- Keep the factory for potential future use, but update it ---
# Note: The AuthDialog will instantiate SimulatedRFIDReader directly as per instructions,
# bypassing this factory for now.

class RFIDReader(QObject):
    """RFID Reader factory and manager (Updated but potentially unused by AuthDialog for now)"""

    # Forward the appropriate signal (now rfid_scanned if using the new simulator directly)
    # Or keep tag_detected if using the PN532Reader part of the factory
    # Let's assume the factory might still provide the PN532, so keep its signal name
    tag_detected = pyqtSignal(str) # From PN532Reader
    rfid_scanned = pyqtSignal(str) # From SimulatedRFIDReader (if used via factory)

    def __init__(self):
        super().__init__()
        self.reader = None
        self.init_reader()

    def init_reader(self):
        """Initialize the appropriate RFID reader"""
        pn532_reader = PN532Reader()
        if pn532_reader.is_available():
            self.reader = pn532_reader
            logger.info("Using PN532 RFID reader")
            # Connect PN532 signal
            self.reader.tag_detected.connect(self.tag_detected)
            # Start PN532 reader
            self.reader.start() # Uses PN532Reader's start method
        else:
            # Fall back to the *new* simulated reader
            self.reader = SimulatedRFIDReader() # Use the new class
            logger.warning("Using NEW simulated RFID reader (no hardware detected)")
            # Connect SimulatedRFIDReader signal
            self.reader.rfid_scanned.connect(self.rfid_scanned) # Connect new signal
            # Start SimulatedRFIDReader
            self.reader.start_reading() # Use the new start method

    def simulate_scan(self, tag_id="SIM_FACTORY_SCAN"):
        """Simulate a tag for testing (only works with simulated reader)"""
        if isinstance(self.reader, SimulatedRFIDReader):
            self.reader.simulate_scan(tag_id) # Use the new method
        else:
            logger.warning("Cannot simulate scan: Real hardware reader is active.")

    def __del__(self):
        """Clean up resources"""
        if self.reader:
            if isinstance(self.reader, PN532Reader):
                self.reader.stop() # Use PN532Reader's stop method
            elif isinstance(self.reader, SimulatedRFIDReader):
                self.reader.stop_reading() # Use the new stop method