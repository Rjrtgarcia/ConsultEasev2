#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConsultEase Central System
Authentication Dialog - Basic UI Structure
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpacerItem, QSizePolicy, QMessageBox, QApplication # Added QMessageBox, QApplication
)
from PyQt6.QtCore import pyqtSlot, QEvent, Qt # Import Qt
from PyQt6.QtGui import QCloseEvent # Import QCloseEvent

# Removed simulated reader import

logger = logging.getLogger(__name__)

class AuthDialog(QDialog):
    """RFID Authentication/Student Verification Dialog using Keyboard Input"""

    def __init__(self, firebase_client=None, parent=None): # Accept firebase_client
        """Initialize the dialog UI elements and RFID buffer."""
        super().__init__(parent)
        self.setWindowTitle("Student Verification")
        self.setModal(True)
        self.rfid_buffer = "" # Initialize RFID buffer
        self.firebase_client = firebase_client # Store the passed client
        self.authenticated_student_id = None # To store ID after successful auth
        self.authenticated_student_name = None # To store name after successful auth

        # --- UI Elements ---
        self.prompt_label = QLabel("Please scan your RFID card")
        self.feedback_label = QLabel("Status: Waiting for scan...")

        # --- Simulation Input Elements (for testing without hardware) ---
        self.sim_id_input = QLineEdit()
        self.sim_id_input.setPlaceholderText("Enter RFID UID to Simulate")
        self.sim_button = QPushButton("Simulate Scan")
        # --- End Simulation Input Elements ---

        # Action Buttons
        self.rescan_button = QPushButton("Re-Scan")
        self.override_button = QPushButton("Manual Override")
        self.cancel_button = QPushButton("Cancel")

        # Initially disable placeholder buttons
        self.rescan_button.setEnabled(False)
        self.override_button.setEnabled(False)

        # --- Layout --- (Mostly unchanged)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.prompt_label)
        main_layout.addWidget(self.feedback_label)

        # --- Simulation Input Layout ---
        sim_layout = QHBoxLayout()
        sim_layout.addWidget(QLabel("Simulate:")) # Label for clarity
        sim_layout.addWidget(self.sim_id_input)
        sim_layout.addWidget(self.sim_button)
        main_layout.addLayout(sim_layout)
        # --- End Simulation Input Layout ---

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.rescan_button)
        button_layout.addWidget(self.override_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        # --- Connections ---
        self.cancel_button.clicked.connect(self.reject)
        # --- Simulation Connection ---
        self.sim_button.clicked.connect(self._on_simulate_scan_clicked)
        # --- End Simulation Connection ---

        # Set minimum size
        self.setMinimumWidth(350)

    # --- Simulation Slot ---
    @pyqtSlot()
    def _on_simulate_scan_clicked(self):
        """
        Handles the click event of the 'Simulate Scan' button.
        Takes the text from the simulation input field and processes it
        as if it were scanned by the RFID reader.
        """
        simulated_id = self.sim_id_input.text().strip()
        if simulated_id:
            logger.info(f"Simulating RFID scan with ID: {simulated_id}")
            self._handle_rfid_scan(simulated_id)
            self.sim_id_input.clear()
        else:
            logger.debug("Simulate scan button clicked with empty input.")
            # Optionally provide feedback, e.g., self.feedback_label.setText("Enter an ID to simulate.")
    # --- End Add Simulation Slot ---

    # @pyqtSlot(str) # Keep this method, but it's no longer a slot
    def _handle_rfid_scan(self, rfid_tag):
        """Handles the processed RFID tag ID, validates against Firebase."""
        if not rfid_tag: # Ignore empty scans
            logger.warning("Empty RFID tag received, ignoring.")
            return

        logger.info(f"RFID scan received: {rfid_tag}. Validating...")
        self.feedback_label.setText(f"Validating RFID: {rfid_tag}...")
        QApplication.processEvents() # Ensure UI updates

        if not self.firebase_client:
            logger.error("Firebase client is not initialized in AuthDialog.")
            self.feedback_label.setText("Error: Database connection not available.")
            QMessageBox.critical(self, "Internal Error", "Firebase client not configured.")
            return

        try:
            student_data = self.firebase_client.get_student_by_rfid(rfid_tag)

            if student_data:
                # Authentication successful
                student_name = student_data.get('name', 'Unknown Student')
                student_id = student_data.get('student_id', None) # Assuming 'student_id' is the key in Firebase

                if not student_id:
                     logger.error(f"Student data found for RFID {rfid_tag}, but 'student_id' field is missing.")
                     self.feedback_label.setText("Error: Incomplete student record.")
                     QMessageBox.warning(self, "Authentication Error", "Student record is incomplete (missing ID).")
                     return # Don't accept if ID is missing

                logger.info(f"Authentication successful for RFID {rfid_tag}. Student: {student_name} (ID: {student_id})")
                self.authenticated_student_id = student_id
                self.authenticated_student_name = student_name
                self.feedback_label.setText(f"Welcome, {student_name}!")
                self.accept() # Close the dialog with Accepted status
            else:
                # Authentication failed - Tag not found
                logger.warning(f"Authentication failed: RFID Tag '{rfid_tag}' not found in database.")
                self.feedback_label.setText("RFID Tag Not Recognized.")
                QMessageBox.warning(self, "Authentication Failed", "RFID Tag not found in the student database.")
                # Do not call self.accept() - allow user to retry or cancel

        except Exception as e:
            logger.exception(f"Error during Firebase lookup for RFID {rfid_tag}: {e}")
            self.feedback_label.setText("Error during validation.")
            QMessageBox.critical(self, "Validation Error", f"An error occurred while checking the RFID tag:\n{e}")
            # Do not call self.accept()

    # --- RFID HID Reader Input Handling ---
    def keyPressEvent(self, event):
        """
        Captures keyboard events globally for this dialog.
        This is used to read input from USB RFID readers that act as
        Keyboard HID devices, typically sending the UID followed by Enter.
        """
        key = event.key()
        text = event.text()

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            logger.debug(f"Enter key pressed. Processing buffer: '{self.rfid_buffer}'")
            self._handle_rfid_scan(self.rfid_buffer)
            self.rfid_buffer = "" # Clear the buffer
            event.accept()
        elif text and text.isprintable(): # Check if it's a printable character
            self.rfid_buffer += text
            logger.debug(f"Character '{text}' appended to buffer. Buffer: '{self.rfid_buffer}'")
            event.accept()
        else:
            # Ignore non-printable keys or pass them to the base class if needed
            logger.debug(f"Ignoring non-printable key: {key}")
            # super().keyPressEvent(event) # Optional: pass other keys up
            event.accept() # Accept to prevent further processing by widgets

    # --- Reset Status on Show/Close ---

    def showEvent(self, event: QEvent):
        """Reset status when the dialog is shown."""
        super().showEvent(event)
        logger.debug("AuthDialog shown.")
        self.rfid_buffer = "" # Clear buffer on show
        self.feedback_label.setText("Status: Waiting for scan...") # Reset status

    def closeEvent(self, event: QCloseEvent):
        """Perform cleanup when the dialog is closed."""
        logger.debug("AuthDialog closing.")
        # No reader stop needed anymore
        super().closeEvent(event)

    # --- Getters for Authenticated User Info ---
    def get_authenticated_student_id(self):
        """Returns the student ID if authentication was successful, otherwise None."""
        return self.authenticated_student_id

    def get_authenticated_student_name(self):
        """Returns the student name if authentication was successful, otherwise None."""
        return self.authenticated_student_name

# Example usage (for testing the dialog directly)
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    dialog = AuthDialog()
    result = dialog.exec() # Use exec_ for modal dialog testing
    if result == QDialog.DialogCode.Accepted:
        print("Dialog Accepted")
    else:
        print("Dialog Rejected/Cancelled")
    sys.exit()