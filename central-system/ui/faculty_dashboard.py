#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConsultEase Central System
Faculty Dashboard UI Component - With Model/View and Filtering
"""

import logging
import re # For parsing MQTT topic
import json # For MQTT payload
from datetime import datetime # For timestamps

# Add necessary imports near the top
from PyQt6.QtCore import (Qt, pyqtSlot, pyqtSignal, QAbstractTableModel,
                          QModelIndex, QSortFilterProxyModel)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QLineEdit, QTextEdit, QGroupBox,
    QTableView, # Changed from QTableWidget
    QHeaderView, QMessageBox, QListWidget # Removed QTableWidgetItem
)

# Import clients (assuming they are accessible via the central system path)
# Adjust imports if your project structure requires it
try:
    from central_system.database.firebase_client import FirebaseClient
except ImportError:
    FirebaseClient = None # Allow running without firebase for testing UI
    logging.warning("Could not import FirebaseClient.") # Use logging directly

try:
    from central_system.comms.mqtt_client import MQTTClient
except ImportError:
    MQTTClient = None # Allow running without MQTT for testing UI
    logging.warning("Could not import MQTTClient.") # Use logging directly

# Define the MQTT topic structure (as derived from config.h concept)
MQTT_STATUS_TOPIC_TEMPLATE = "consultease/faculty/{}/status"
MQTT_REQUEST_TOPIC = "consultease/requests/new" # Topic for new requests

logger = logging.getLogger(__name__)

# --- Custom Table Model ---
class FacultyTableModel(QAbstractTableModel):
    """Model to hold faculty data for the QTableView."""
    # Define column indices consistently
    COL_NAME = 0
    COL_DEPT = 1
    COL_STATUS = 2
    HEADERS = ["Name", "Department", "Status"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = [] # Internal data store: List of dictionaries, one per faculty member.
        self._id_map = {} # Cache mapping faculty_id to its index in self._data for faster updates.

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns in the model."""
        return len(self.HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Returns the data for the given index and role."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if not (0 <= row < self.rowCount()):
             return None

        faculty_member = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_NAME:
                return faculty_member.get('name', 'N/A')
            elif col == self.COL_DEPT:
                return faculty_member.get('dept', 'N/A')
            elif col == self.COL_STATUS:
                return faculty_member.get('status', 'Unknown')
        # Add more roles if needed (e.g., for tooltips, alignment)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Returns the header data for the given section and orientation."""
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def load_data(self, faculty_list_data: dict):
        """Loads data from a dictionary {faculty_id: data}."""
        logger.info(f"Model: Loading {len(faculty_list_data)} faculty members.")
        self.beginResetModel() # Signal that the model is about to change drastically
        self._data = []
        self._id_map = {}
        for i, (faculty_id, data) in enumerate(faculty_list_data.items()):
            self._data.append({
                'id': faculty_id,
                'name': data.get('name', 'N/A'),
                'dept': data.get('department', 'N/A'),
                'status': "Offline" # Default status
            })
            self._id_map[faculty_id] = i
        self.endResetModel() # Signal that the model has changed

    def update_status(self, faculty_id: str, new_status: str):
        """Updates the status for a specific faculty member."""
        if faculty_id in self._id_map:
            row_index = self._id_map[faculty_id]
            if 0 <= row_index < len(self._data):
                self._data[row_index]['status'] = new_status
                # Emit dataChanged signal for the specific cell
                model_index = self.index(row_index, self.COL_STATUS)
                self.dataChanged.emit(model_index, model_index, [Qt.ItemDataRole.DisplayRole])
                logger.debug(f"Model: Updated status for {faculty_id} to {new_status} at row {row_index}")
                return True
            else:
                 logger.error(f"Model: Row index {row_index} out of bounds for faculty_id {faculty_id}")
                 return False
        else:
            logger.warning(f"Model: Attempted to update status for unknown faculty_id: {faculty_id}")
            return False

    def get_faculty_data_by_row(self, row):
        """Returns the dictionary for the faculty member at the given row."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

# --- Custom Filter Proxy Model ---
class FacultyFilterProxyModel(QSortFilterProxyModel):
    """Proxy model to handle text search and status filtering."""
    # Define column indices consistently (matching source model)
    COL_NAME = 0
    COL_DEPT = 1
    COL_STATUS = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_filter_enabled = False
        self._status_column_index = self.COL_STATUS # Status is in the 3rd column (index 2)
        self._filter_status_value = "available" # Status to filter for (lowercase)

    def set_status_filter_enabled(self, enabled: bool):
        """Enable or disable the status filter."""
        if self._status_filter_enabled != enabled:
            self._status_filter_enabled = enabled
            self.invalidateFilter() # Re-apply the filter

    def filterAcceptsRow(self, source_row, source_parent):
        """Overrides the base class filter logic."""
        # 1. Check text filter (applied via setFilterRegularExpression)
        text_accepts = super().filterAcceptsRow(source_row, source_parent)
        if not text_accepts:
            return False # If text filter rejects, no need to check status

        # 2. Check status filter (if enabled)
        if self._status_filter_enabled:
            source_model = self.sourceModel()
            if source_model:
                status_index = source_model.index(source_row, self._status_column_index, source_parent)
                status_data = source_model.data(status_index, Qt.ItemDataRole.DisplayRole)
                if status_data:
                    # Check if the status matches the desired filter value (case-insensitive)
                    status_accepts = (str(status_data).lower() == self._filter_status_value)
                    return status_accepts # Return based only on status if filter is enabled
                else:
                    return False # Row doesn't have status data, reject if filtering by status
            else:
                 return False # No source model, reject

        # If status filter is not enabled, accept based on text filter result
        return True

# --- FacultyDashboard Class ---
class FacultyDashboard(QWidget):
    """
    Faculty Dashboard UI. Displays faculty list, status, and allows interaction.
    Integrates Firebase for data fetching and MQTT for real-time status updates.
    Uses QTableView with custom models for filtering and sorting.
    """
    # COL_NAME = 0 # Using model's constants now
    # COL_DEPT = 1
    # COL_STATUS = 2

    def __init__(self, firebase_client: FirebaseClient = None, mqtt_client: MQTTClient = None, student_id: str = None, parent=None): # Added student_id parameter
        """Initialize the dashboard UI elements."""
        super().__init__(parent)
        self.firebase_client = firebase_client
        self.mqtt_client = mqtt_client
        # self.faculty_status = {} # No longer needed, model holds the data
        self.student_id = student_id if student_id else "UNKNOWN_STUDENT_ID" # Store the passed student ID, with a fallback
        self.MAX_NOTIFICATIONS = 50

        self.setWindowTitle("Faculty Dashboard")

        # --- Model Setup ---
        self.table_model = FacultyTableModel(self)
        self.proxy_model = FacultyFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.table_model)
        # Configure proxy model defaults
        self.proxy_model.setFilterKeyColumn(-1) # Search across all columns
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._init_ui() # UI setup needs models
        self._connect_signals()
        self._init_mqtt_connection()

    def _init_ui(self):
        """Set up the main layout and widgets, using QTableView."""
        main_layout = QGridLayout(self)
        main_layout.setSpacing(15)

        # --- Search and Filter ---
        search_filter_group = QGroupBox("Search & Filter")
        search_filter_layout = QHBoxLayout()
        search_filter_group.setLayout(search_filter_layout)

        # Make search input an instance variable
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Faculty (Name, Dept)...")
        search_filter_layout.addWidget(self.search_input)

        # Make filter button an instance variable and checkable
        self.filter_button = QPushButton("Show Available Only")
        self.filter_button.setCheckable(True)
        search_filter_layout.addWidget(self.filter_button)

        main_layout.addWidget(search_filter_group, 0, 0, 1, 2)

        # --- Faculty Availability Panel ---
        availability_group = QGroupBox("Faculty Availability")
        availability_layout = QVBoxLayout()
        availability_group.setLayout(availability_layout)

        # --- Faculty Table View --- (Changed from QTableWidget)
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model) # Set the PROXY model on the view

        # Configure Table View Appearance
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setSortingEnabled(True) # Allow sorting by clicking headers
        self.table_view.sortByColumn(FacultyTableModel.COL_NAME, Qt.SortOrder.AscendingOrder) # Default sort

        # Configure Header Resizing (use model's column constants)
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(FacultyTableModel.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(FacultyTableModel.COL_DEPT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(FacultyTableModel.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)

        availability_layout.addWidget(self.table_view)

        # Remove old buttons if not needed, or adapt them
        # availability_buttons_layout = QHBoxLayout()
        # sort_button = QPushButton("Sort by Name") # Sorting is now handled by clicking headers
        # filter_dept_button = QPushButton("Filter by Department") # Could add more filters later
        # availability_buttons_layout.addWidget(filter_dept_button)
        # availability_buttons_layout.addStretch()
        # availability_layout.addLayout(availability_buttons_layout)

        main_layout.addWidget(availability_group, 1, 0)

        # --- Consultation Request Module --- (Keep as is, but selection needs update)
        request_group = QGroupBox("Consultation Request")
        request_layout = QVBoxLayout()
        request_group.setLayout(request_layout)

        self.request_label = QLabel("Select a faculty member to request consultation.") # Made instance var
        request_layout.addWidget(self.request_label)

        self.request_message_input = QTextEdit()
        self.request_message_input.setPlaceholderText("Enter your consultation request message here...")
        self.request_message_input.setFixedHeight(80)
        request_layout.addWidget(self.request_message_input)

        self.submit_request_button = QPushButton("Submit Request")
        self.submit_request_button.setEnabled(False) # Initially disabled until selection
        request_layout.addWidget(self.submit_request_button, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(request_group, 2, 0)

        # --- Real-Time Notifications --- (Keep as is)
        notifications_group = QGroupBox("Notifications")
        notifications_layout = QVBoxLayout()
        notifications_group.setLayout(notifications_layout)

        self.notification_list = QListWidget()
        self.notification_list.setWordWrap(True)
        notifications_layout.addWidget(self.notification_list)

        main_layout.addWidget(notifications_group, 1, 1, 2, 1)

        # --- Layout Stretching --- (Keep as is)
        main_layout.setColumnStretch(0, 2)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(1, 3)
        main_layout.setRowStretch(2, 1)

        logger.info("FacultyDashboard UI initialized with QTableView and Models.")

    def _connect_signals(self):
        """Connect signals from MQTT, UI elements, and models."""
        # --- MQTT Signals --- (Keep existing logic)
        if self.mqtt_client:
            try:
                if hasattr(self.mqtt_client, 'message_received'):
                    self.mqtt_client.message_received.connect(self._handle_mqtt_message)
                else:
                    logger.warning("MQTT client is missing 'message_received' signal.")

                if hasattr(self.mqtt_client, 'connected'):
                    # Load list AFTER UI is fully set up and models exist
                    self.mqtt_client.connected.connect(self.load_faculty_list)
                else:
                    logger.warning("MQTT client is missing 'connected' signal.")
                logger.info("MQTT signals connected (if available).")
            except Exception as e:
                 logger.error(f"Unexpected error connecting MQTT signals: {e}", exc_info=True)
        else:
            logger.warning("MQTT client not available, skipping signal connection.")

        # --- Search and Filter Signals ---
        if hasattr(self, 'search_input'):
            self.search_input.textChanged.connect(self.proxy_model.setFilterRegularExpression)
            logger.info("Search input signal connected.")
        else:
            logger.error("Could not connect search_input signal - widget not found.")

        if hasattr(self, 'filter_button'):
            self.filter_button.toggled.connect(self._apply_status_filter)
            logger.info("Filter button signal connected.")
        else:
            logger.error("Could not connect filter_button signal - widget not found.")

        # --- Consultation Request Signals ---
        if hasattr(self, 'submit_request_button'):
            self.submit_request_button.clicked.connect(self._submit_request)
            logger.info("Consultation request button signal connected.")
        else:
             logger.error("Could not connect submit_request_button signal - button not found.")

        # --- Table View Selection Signal ---
        if hasattr(self, 'table_view'):
             selection_model = self.table_view.selectionModel()
             if selection_model:
                  # Use the correct signal signature for selectionChanged
                  selection_model.selectionChanged.connect(self._handle_selection_change)
                  logger.info("Table view selection signal connected.")
             else:
                  logger.error("Could not get selection model from table_view.")
        else:
             logger.error("Could not connect table_view selection signal - view not found.")


    # --- New Slot for Filter Button ---
    @pyqtSlot(bool)
    def _apply_status_filter(self, checked):
        """Applies or removes the status filter based on the button state."""
        logger.info(f"Status filter toggled: {'Enabled' if checked else 'Disabled'}")
        self.proxy_model.set_status_filter_enabled(checked)

    # --- New Slot for Table Selection ---
    # Corrected signature for selectionChanged signal
    @pyqtSlot('QItemSelection', 'QItemSelection')
    def _handle_selection_change(self, selected, deselected):
        """Enable/disable request button based on table selection."""
        # Check if the selection model actually has a current index selected
        selection_model = self.table_view.selectionModel() # Get the current selection model
        has_selection = selection_model is not None and selection_model.hasSelection()
        self.submit_request_button.setEnabled(has_selection)

        if has_selection:
             # Get selected row from the VIEW (proxy model index)
             # Use currentIndex() which is usually valid when hasSelection is true
             proxy_index = selection_model.currentIndex()
             if proxy_index.isValid(): # Ensure the index is valid before mapping
                 # Map proxy index to SOURCE model index
                 source_index = self.proxy_model.mapToSource(proxy_index)
                 source_row = source_index.row()
                 faculty_data = self.table_model.get_faculty_data_by_row(source_row)
                 if faculty_data:
                      self.request_label.setText(f"Request consultation with: {faculty_data.get('name', 'N/A')}")
                 else:
                      self.request_label.setText("Select a faculty member to request consultation.")
             else:
                  # Handle cases where selection exists but currentIndex is invalid (less common)
                  self.request_label.setText("Select a faculty member to request consultation.")
                  self.submit_request_button.setEnabled(False)
        else:
             self.request_label.setText("Select a faculty member to request consultation.")


    def _init_mqtt_connection(self):
        """Initiate connection to the MQTT broker."""
        if self.mqtt_client:
            logger.info("Attempting to connect to MQTT broker...")
            try:
                self.mqtt_client.connect_to_broker()
                # Start the MQTT client's network loop in a background thread.
                # This handles reconnects and processes incoming messages without blocking the UI.
                if hasattr(self.mqtt_client, 'client') and callable(getattr(self.mqtt_client.client, 'loop_start', None)):
                    self.mqtt_client.client.loop_start()
                    logger.info("MQTT client network loop started.")
                else:
                    logger.warning("MQTT client or its 'client' attribute missing 'loop_start' method.")
            except Exception as e:
                logger.error(f"Error during MQTT connection or loop start: {e}", exc_info=True)
        else:
            logger.warning("MQTT client not available, skipping connection.")


    def load_faculty_list(self):
        """Fetch faculty data and load it into the FacultyTableModel."""
        if not self.firebase_client:
            logger.warning("Firebase client not available. Cannot load faculty list.")
            # Optionally display a message in the view (less direct with model/view)
            # Maybe add a status label elsewhere? For now, just log.
            self.table_model.load_data({}) # Clear the model
            return

        logger.info("Loading faculty list from Firebase...")
        try:
            faculty_list_data = self.firebase_client.get_all_faculty()

            if not faculty_list_data:
                logger.warning("No faculty data found in Firebase.")
                self.table_model.load_data({}) # Load empty data
                return

            # Load data into the source model
            self.table_model.load_data(faculty_list_data)
            logger.info(f"Successfully loaded {self.table_model.rowCount()} faculty members into model.")

            # Subscribe to MQTT topics AFTER data is loaded into the model
            if self.mqtt_client and hasattr(self.mqtt_client, 'subscribe'):
                 for faculty_id in faculty_list_data.keys():
                      try:
                           status_topic = MQTT_STATUS_TOPIC_TEMPLATE.format(faculty_id)
                           self.mqtt_client.subscribe(status_topic)
                           logger.debug(f"Subscribed to {status_topic}")
                      except Exception as e:
                           logger.error(f"Error subscribing to topic {status_topic}: {e}")

            # Adjust columns after model reset (view should update automatically)
            # self.table_view.resizeColumnsToContents() # May not be needed if resize modes are set

        except AttributeError as e:
             logger.error(f"Firebase client is missing expected method (e.g., get_all_faculty): {e}", exc_info=True)
             self.table_model.load_data({}) # Clear the model on error
             # Handle error display if needed
        except Exception as e:
            logger.error(f"Error loading faculty list from Firebase: {e}", exc_info=True)
            self.table_model.load_data({}) # Clear the model on error
            # Handle error display if needed

    @pyqtSlot(str, str)
    def _handle_mqtt_message(self, topic: str, payload: str):
        """Handle incoming MQTT messages, updating the FacultyTableModel."""
        logger.debug(f"MQTT message received: Topic='{topic}', Payload='{payload}'")

        match = re.match(r"consultease/faculty/([^/]+)/status", topic)
        if match:
            faculty_id = match.group(1)
            new_status = payload

            # Update the source model
            updated = self.table_model.update_status(faculty_id, new_status)

            if updated:
                # Find the faculty name from the model for the notification
                faculty_data = None
                if faculty_id in self.table_model._id_map: # Access internal map for name lookup
                    row_index = self.table_model._id_map[faculty_id]
                    faculty_data = self.table_model.get_faculty_data_by_row(row_index)

                faculty_name = faculty_data.get('name', faculty_id) if faculty_data else faculty_id
                logger.info(f"Updated status via MQTT for faculty {faculty_id} ({faculty_name}) to '{new_status}'")
                self.add_notification(f"Faculty {faculty_name} is now {new_status}")
            # else: # Warning already logged by update_status
            #     logger.warning(f"Received status update for unknown/unmapped faculty ID: {faculty_id}")

    def add_notification(self, message: str):
        """Adds a timestamped notification message to the list."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.notification_list.insertItem(0, formatted_message) # Insert at the top

        # Limit the number of items
        if self.notification_list.count() > self.MAX_NOTIFICATIONS:
            self.notification_list.takeItem(self.notification_list.count() - 1) # Remove the oldest item

    @pyqtSlot()
    def _submit_request(self):
        """Handles consultation request using selected faculty from the table."""
        if not self.mqtt_client or not self.firebase_client:
            QMessageBox.warning(self, "Error", "System components (MQTT/Firebase) not available.")
            logger.error("Attempted to submit request but MQTT or Firebase client is missing.")
            return

        request_text = self.request_message_input.toPlainText().strip()
        if not request_text:
            QMessageBox.warning(self, "Input Error", "Please enter your consultation request message.")
            return

        # Get selected faculty from the TABLE VIEW's selection model
        selection_model = self.table_view.selectionModel()
        if not selection_model or not selection_model.hasSelection():
             QMessageBox.warning(self, "Selection Error", "Please select a faculty member from the list.")
             return

        # Get the proxy index, map to source index, then get data from source model
        proxy_index = selection_model.currentIndex()
        if not proxy_index.isValid(): # Check if current index is valid
             QMessageBox.warning(self, "Selection Error", "Invalid selection index.")
             logger.warning("Submit request called with invalid current index.")
             return

        source_index = self.proxy_model.mapToSource(proxy_index)
        source_row = source_index.row()
        selected_faculty_data = self.table_model.get_faculty_data_by_row(source_row)

        if not selected_faculty_data:
             QMessageBox.critical(self, "Error", "Could not retrieve data for the selected faculty.")
             logger.error(f"Failed to get faculty data for selected source row: {source_row}")
             return

        selected_faculty_id = selected_faculty_data.get('id')
        selected_faculty_name = selected_faculty_data.get('name', 'N/A')

        if not selected_faculty_id:
             QMessageBox.critical(self, "Error", "Selected faculty data is missing ID.")
             logger.error(f"Selected faculty data missing ID at source row: {source_row}")
             return

        logger.info(f"Submitting request for faculty: {selected_faculty_name} (ID: {selected_faculty_id})")

        timestamp = datetime.now().isoformat()
        student_id = self.student_id

        # --- Prepare Payloads (Add faculty_id) ---
        mqtt_payload = {
            "student_id": student_id,
            "faculty_id": selected_faculty_id, # Add faculty ID
            "request_text": request_text,
            "timestamp": timestamp
        }
        firebase_data = {
            "student_id": student_id,
            "faculty_id": selected_faculty_id, # Add faculty ID
            "request_text": request_text,
            "timestamp": timestamp,
            "status": "pending"
        }

        # --- Serialize MQTT Payload ---
        try:
            mqtt_payload_json = json.dumps(mqtt_payload)
        except TypeError as e:
             QMessageBox.critical(self, "Error", f"Could not serialize request data: {e}")
             logger.error(f"JSON serialization error for MQTT payload: {e}")
             return

        # --- Attempt Publish and Log ---
        mqtt_success = False
        firebase_success = False

        try:
            logger.info(f"Publishing request to MQTT topic: {MQTT_REQUEST_TOPIC}")
            publish_result = self.mqtt_client.publish(topic=MQTT_REQUEST_TOPIC, payload=mqtt_payload_json)
            if isinstance(publish_result, tuple) and publish_result[0] == 0:
                 mqtt_success = True
                 logger.info(f"MQTT publish successful (mid={publish_result[1]}).")
            elif publish_result is True:
                 mqtt_success = True
                 logger.info("MQTT publish successful.")
            else:
                 logger.error(f"MQTT publish failed. Result: {publish_result}")
        except AttributeError:
             logger.error("MQTT client does not have a 'publish' method.", exc_info=True)
             QMessageBox.critical(self, "Error", "MQTT client is not configured correctly (missing publish method).")
             return
        except Exception as e:
            logger.error(f"Error publishing request via MQTT: {e}", exc_info=True)

        try:
            logger.info("Logging request to Firebase collection: requests")
            log_result = self.firebase_client.log_request(firebase_data)
            if log_result:
                firebase_success = True
                logger.info(f"Firebase logging successful (Doc ID: {log_result}).")
            else:
                logger.error("Firebase logging failed (log_request returned None).")
        except AttributeError:
             logger.error("Firebase client does not have a 'log_request' method.", exc_info=True)
             QMessageBox.critical(self, "Error", "Firebase client is not configured correctly (missing log_request method).")
             firebase_success = False
        except Exception as e:
            logger.error(f"Error logging request to Firebase: {e}", exc_info=True)
            firebase_success = False

        # --- Provide User Feedback ---
        if mqtt_success and firebase_success:
            self.request_message_input.clear()
            self.add_notification(f"Consultation request for {selected_faculty_name} sent.")
            QMessageBox.information(self, "Success", f"Consultation request for {selected_faculty_name} sent successfully!")
        else:
            error_details = []
            if not mqtt_success: error_details.append("MQTT publish failed")
            if not firebase_success: error_details.append("Firebase logging failed")
            error_string = '; '.join(error_details)
            self.add_notification(f"Error sending request for {selected_faculty_name}: {error_string}")
            QMessageBox.warning(self, "Request Failed", f"Failed to send consultation request for {selected_faculty_name}.\nDetails: {error_string}\nPlease try again or contact support.")


# --- Main execution block ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    import random # Import random for mock publish
    from PyQt6.QtCore import QTimer # Import QTimer for mock client

    logging.basicConfig(level=logging.INFO)

    # --- Mock Clients for Standalone Testing ---
    class MockFirebaseClient:
        """Mock Firebase client for standalone UI testing."""
        def get_all_faculty(self):
            """Simulates fetching faculty data."""
            logger.info("Using MockFirebaseClient.get_all_faculty()")
            return {
                "faculty001": {"name": "Dr. Alice Smith", "department": "Computer Science"},
                "faculty002": {"name": "Prof. Bob Jones", "department": "Physics"},
                "faculty003": {"name": "Dr. Carol White", "department": "Mathematics"},
                "faculty004": {"name": "Dr. David Lee", "department": "Computer Science"},
            }
        def log_request(self, request_data):
            """Simulates logging a request."""
            logger.info(f"Using MockFirebaseClient.log_request() with data: {request_data}")
            return f"mock_req_{int(datetime.now().timestamp())}"

    class MockMQTTClient:
        """Mock MQTT client for standalone UI testing."""
        # Define signals properly
        message_received = pyqtSignal(str, str) # Signal emitted when a mock message is 'received'
        connected = pyqtSignal()

        def __init__(self, *args, **kwargs):
            self.client = self # Mock the paho client attribute needed for loop_start
            logger.info("Using MockMQTTClient")
            self._timer = None # Timer for simulating incoming messages

        def connect_to_broker(self):
            """Simulates connecting to the broker."""
            logger.info("MockMQTT: connect_to_broker called")
            QTimer.singleShot(500, self.connected.emit) # Emit connected signal after delay

        def subscribe(self, topic):
            """Simulates subscribing to a topic."""
            logger.info(f"MockMQTT: subscribe called for topic: {topic}")

        def publish(self, topic, payload, qos=0, retain=False):
            """Simulates publishing a message."""
            logger.info(f"MockMQTT: publish called for topic: {topic}, Payload: {str(payload)[:100]}...")
            if topic == MQTT_REQUEST_TOPIC:
                # Paho client returns (0, mid) on success
                return (0, random.randint(1, 10000))
            return (1, 0) # Simulate failure for other topics

        def loop_start(self):
             """Simulates starting the MQTT network loop."""
             logger.info(f"MockMQTT: loop_start called")
             if not self._timer: # Avoid creating multiple timers
                 self._timer = QTimer()
                 self._timer.timeout.connect(self._simulate_message)
                 self._timer.start(3000) # Send a message every 3 seconds

        def _simulate_message(self):
            """Generates and emits a simulated MQTT status message."""
            faculty_ids = ["faculty001", "faculty002", "faculty003", "faculty004"]
            statuses = ["Available", "Unavailable", "Present", "Offline"]
            random_id = random.choice(faculty_ids)
            random_status = random.choice(statuses)
            topic = MQTT_STATUS_TOPIC_TEMPLATE.format(random_id)
            logger.info(f"MockMQTT: Simulating message: {topic} -> {random_status}")
            try:
                self.message_received.emit(topic, random_status)
            except RuntimeError as e:
                 logger.error(f"Error emitting mock message (maybe app closed?): {e}")
                 self.loop_stop() # Stop timer if emitting fails

        def loop_stop(self):
            """Simulates stopping the MQTT network loop."""
            logger.info(f"MockMQTT: loop_stop called")
            if hasattr(self, '_timer') and self._timer:
                self._timer.stop()
                self._timer = None # Clear timer reference

    # --- Run the Application ---
    app = QApplication(sys.argv)

    # Instantiate mock clients
    mock_firebase = MockFirebaseClient()
    mock_mqtt = MockMQTTClient()

    # Instantiate the dashboard with mocks
    dashboard = FacultyDashboard(firebase_client=mock_firebase, mqtt_client=mock_mqtt)
    dashboard.show()

    # Ensure the mock MQTT loop stops when the app closes
    app.aboutToQuit.connect(mock_mqtt.loop_stop)

    sys.exit(app.exec())