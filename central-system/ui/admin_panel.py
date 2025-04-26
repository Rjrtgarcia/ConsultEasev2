#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConsultEase Central System
Admin Panel UI Component - Scalable Structure with Tabs
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableView,
    QDialog, QLineEdit, QFormLayout, QGroupBox, QMessageBox,
    QDialogButtonBox, QApplication, QHeaderView, QTabWidget # Added QTabWidget
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QIcon # Consider adding icons later

# Assuming FirebaseClient is accessible or passed appropriately
# from ..database.firebase_client import FirebaseClient # Adjust import path as needed

logger = logging.getLogger(__name__)

# ==============================================================================
# Faculty Data Model
# ==============================================================================

class FacultyTableModel(QAbstractTableModel):
    """
    A basic table model for managing faculty data in a QTableView.
    Fetches data from Firebase.
    """
    _HEADERS = ["ID", "Name", "Department", "Contact", "RFID Tag", "Status"]
    _COLUMN_MAP = {
        "ID": "id",
        "Name": "name",
        "Department": "department",
        "Contact": "contact",
        "RFID Tag": "rfid_tag",
        "Status": "status"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._faculty_data = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._faculty_data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            try:
                faculty_dict = self._faculty_data[row]
                header = self._HEADERS[col]
                data_key = self._COLUMN_MAP.get(header)
                if data_key:
                    value = faculty_dict.get(data_key, "")
                    return str(value) if value is not None else ""
                else:
                    return None
            except IndexError:
                logger.error(f"IndexError accessing faculty data at row {row}")
                return None
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._HEADERS):
                    return self._HEADERS[section]
        return None

    def load_data(self, firebase_client):
        """Fetches faculty data from Firebase and updates the model."""
        logger.info("Attempting to load faculty data from Firebase...")
        if not firebase_client or firebase_client.is_offline():
            logger.warning("Firebase client not available or offline. Cannot load faculty data.")
            self.beginResetModel()
            self._faculty_data = []
            self.endResetModel()
            QMessageBox.warning(None, "Offline", "Cannot connect to database. Please check connection.")
            return False

        self.beginResetModel()
        try:
            faculty_list = firebase_client.get_all_faculty()
            if faculty_list is not None:
                self._faculty_data = faculty_list
                logger.info(f"Successfully loaded {len(self._faculty_data)} faculty records.")
            else:
                self._faculty_data = []
                logger.error("Failed to load faculty data from Firebase (returned None).")
                QMessageBox.critical(None, "Error", "Failed to load faculty data from database.")
        except Exception as e:
            self._faculty_data = []
            logger.exception(f"Exception while loading faculty data: {e}")
            QMessageBox.critical(None, "Error", f"An error occurred while loading faculty data:\n{e}")
        finally:
            self.endResetModel()
            return bool(self._faculty_data)

    def get_faculty_by_row(self, row):
        """Returns the data for a specific row (e.g., as a dict)."""
        if 0 <= row < self.rowCount():
            return self._faculty_data[row]
        return None

# ==============================================================================
# Student Data Model (NEW)
# ==============================================================================

class StudentTableModel(QAbstractTableModel):
    """
    Table model for managing student data.
    """
    _HEADERS = ["ID", "Student ID", "Name", "RFID Tag"] # Example headers
    _COLUMN_MAP = {
        "ID": "id", # Firestore document ID
        "Student ID": "student_id",
        "Name": "name",
        "RFID Tag": "rfid_tag"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._student_data = [] # List of student dictionaries

    def rowCount(self, parent=QModelIndex()):
        return len(self._student_data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            try:
                student_dict = self._student_data[row]
                header = self._HEADERS[col]
                data_key = self._COLUMN_MAP.get(header)
                if data_key:
                    value = student_dict.get(data_key, "")
                    return str(value) if value is not None else ""
                else:
                    return None
            except IndexError:
                logger.error(f"IndexError accessing student data at row {row}")
                return None
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._HEADERS):
                    return self._HEADERS[section]
        return None

    def load_data(self, firebase_client):
        """Fetches student data from Firebase and updates the model."""
        logger.info("Attempting to load student data from Firebase...")
        if not firebase_client or firebase_client.is_offline():
            logger.warning("Firebase client not available or offline. Cannot load student data.")
            self.beginResetModel()
            self._student_data = []
            self.endResetModel()
            QMessageBox.warning(None, "Offline", "Cannot connect to database. Please check connection.")
            return False

        self.beginResetModel()
        try:
            # *** Use the correct Firebase client method ***
            student_list = firebase_client.get_all_students()
            if student_list is not None:
                self._student_data = student_list
                logger.info(f"Successfully loaded {len(self._student_data)} student records.")
            else:
                self._student_data = []
                logger.error("Failed to load student data from Firebase (returned None).")
                QMessageBox.critical(None, "Error", "Failed to load student data from database.")
        except Exception as e:
            self._student_data = []
            logger.exception(f"Exception while loading student data: {e}")
            QMessageBox.critical(None, "Error", f"An error occurred while loading student data:\n{e}")
        finally:
            self.endResetModel()
            return bool(self._student_data)

    def get_student_by_row(self, row):
        """Returns the data for a specific student row."""
        if 0 <= row < self.rowCount():
            return self._student_data[row]
        return None


# ==============================================================================
# Faculty Add/Edit Dialog
# ==============================================================================

class FacultyDialog(QDialog):
    """
    Dialog for adding or editing faculty details.
    """
    def __init__(self, faculty_data=None, parent=None):
        super().__init__(parent)
        self.faculty_data = faculty_data or {}
        self.setWindowTitle("Add Faculty" if not faculty_data else "Edit Faculty")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(self.faculty_data.get('name', ''))
        self.dept_input = QLineEdit(self.faculty_data.get('department', ''))
        self.contact_input = QLineEdit(self.faculty_data.get('contact', ''))
        self.rfid_input = QLineEdit(self.faculty_data.get('rfid_tag', ''))
        self.status_input = QLineEdit(self.faculty_data.get('status', 'Available'))

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Department:", self.dept_input)
        form_layout.addRow("Contact:", self.contact_input)
        form_layout.addRow("RFID Tag:", self.rfid_input)
        form_layout.addRow("Status:", self.status_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Name cannot be empty.")
            return None
        # Add more validation as needed (e.g., RFID format)

        return {
            'name': self.name_input.text().strip(),
            'department': self.dept_input.text().strip(),
            'contact': self.contact_input.text().strip(),
            'rfid_tag': self.rfid_input.text().strip(),
            'status': self.status_input.text().strip() or 'Available',
        }

    def accept(self):
        if self.get_data():
            super().accept()

# ==============================================================================
# Student Add/Edit Dialog (NEW)
# ==============================================================================

class StudentDialog(QDialog):
    """
    Dialog for adding or editing student details.
    """
    def __init__(self, student_data=None, parent=None):
        super().__init__(parent)
        self.student_data = student_data or {}
        self.setWindowTitle("Add Student" if not student_data else "Edit Student")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Fields for Student: Student ID, Name, RFID Tag
        self.student_id_input = QLineEdit(self.student_data.get('student_id', ''))
        self.name_input = QLineEdit(self.student_data.get('name', ''))
        self.rfid_input = QLineEdit(self.student_data.get('rfid_tag', ''))

        form_layout.addRow("Student ID:", self.student_id_input)
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("RFID Tag:", self.rfid_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        """Retrieves and validates data from the dialog."""
        student_id = self.student_id_input.text().strip()
        name = self.name_input.text().strip()
        rfid = self.rfid_input.text().strip()

        if not student_id:
            QMessageBox.warning(self, "Input Error", "Student ID cannot be empty.")
            return None
        if not name:
            QMessageBox.warning(self, "Input Error", "Name cannot be empty.")
            return None
        # Add RFID validation if needed

        return {
            'student_id': student_id,
            'name': name,
            'rfid_tag': rfid,
        }

    def accept(self):
        """Validate data before accepting."""
        if self.get_data():
            super().accept()


# ==============================================================================
# Main Admin Panel Widget
# ==============================================================================

class AdminPanel(QWidget):
    """
    Admin panel widget for managing faculty and student details using tabs.
    """
    def __init__(self, db_client=None, parent=None):
        super().__init__(parent)
        self.db_client = db_client
        self.setWindowTitle("Admin Panel")
        self.setMinimumSize(700, 500) # Adjusted size for tabs

        self.init_ui()
        self._load_initial_data() # Load data for both tabs

    def init_ui(self):
        """Set up the user interface components with tabs."""
        main_layout = QVBoxLayout(self)

        # Create Tab Widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- Create Faculty Tab ---
        self.faculty_tab = QWidget()
        self.setup_faculty_tab() # Encapsulate faculty UI setup
        self.tab_widget.addTab(self.faculty_tab, "Faculty Management")

        # --- Create Student Tab ---
        self.student_tab = QWidget()
        self.setup_student_tab() # Encapsulate student UI setup
        self.tab_widget.addTab(self.student_tab, "Student Management")

        logger.info("AdminPanel UI initialized with Tabs.")

    def setup_faculty_tab(self):
        """Sets up the UI elements for the Faculty Management tab."""
        faculty_layout = QVBoxLayout(self.faculty_tab) # Layout for the faculty tab widget

        # Toolbar
        toolbar_layout = QHBoxLayout()
        self.faculty_refresh_button = QPushButton("Refresh List")
        self.faculty_add_button = QPushButton("Add Faculty")
        self.faculty_edit_button = QPushButton("Edit Selected")
        self.faculty_delete_button = QPushButton("Delete Selected")

        toolbar_layout.addWidget(self.faculty_refresh_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.faculty_add_button)
        toolbar_layout.addWidget(self.faculty_edit_button)
        toolbar_layout.addWidget(self.faculty_delete_button)

        faculty_layout.addLayout(toolbar_layout)

        # Faculty Table View
        self.faculty_table_view = QTableView()
        self.faculty_model = FacultyTableModel()
        self.faculty_table_view.setModel(self.faculty_model)

        # Table view settings (same as before)
        self.faculty_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.faculty_table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.faculty_table_view.verticalHeader().setVisible(False)
        self.faculty_table_view.horizontalHeader().setStretchLastSection(True)
        self.faculty_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.faculty_table_view.setSortingEnabled(True)
        self.faculty_table_view.setColumnHidden(0, True) # Hide Firestore ID

        faculty_layout.addWidget(self.faculty_table_view)

        # Connect faculty buttons to slots
        self.faculty_refresh_button.clicked.connect(self._refresh_faculty_data)
        self.faculty_add_button.clicked.connect(self._add_faculty)
        self.faculty_edit_button.clicked.connect(self._edit_faculty)
        self.faculty_delete_button.clicked.connect(self._delete_faculty)

    def setup_student_tab(self):
        """Sets up the UI elements for the Student Management tab."""
        student_layout = QVBoxLayout(self.student_tab) # Layout for the student tab widget

        # Toolbar
        toolbar_layout = QHBoxLayout()
        self.student_refresh_button = QPushButton("Refresh List")
        self.student_add_button = QPushButton("Add Student")
        self.student_edit_button = QPushButton("Edit Selected")
        self.student_delete_button = QPushButton("Delete Selected")

        toolbar_layout.addWidget(self.student_refresh_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.student_add_button)
        toolbar_layout.addWidget(self.student_edit_button)
        toolbar_layout.addWidget(self.student_delete_button)

        student_layout.addLayout(toolbar_layout)

        # Student Table View
        self.student_table_view = QTableView()
        self.student_model = StudentTableModel() # Create instance of student model
        self.student_table_view.setModel(self.student_model)

        # Table view settings
        self.student_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.student_table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.student_table_view.verticalHeader().setVisible(False)
        self.student_table_view.horizontalHeader().setStretchLastSection(True)
        self.student_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.student_table_view.setSortingEnabled(True)
        self.student_table_view.setColumnHidden(0, True) # Hide Firestore ID

        student_layout.addWidget(self.student_table_view)

        # Connect student buttons to slots (NEW)
        self.student_refresh_button.clicked.connect(self._refresh_students)
        self.student_add_button.clicked.connect(self._add_student)
        self.student_edit_button.clicked.connect(self._edit_student)
        self.student_delete_button.clicked.connect(self._delete_student)


    def _load_initial_data(self):
        """Loads initial data for both faculty and students."""
        self._refresh_faculty_data()
        self._refresh_students()

    # --- Faculty Action Slots (Renamed for clarity) ---

    def _refresh_faculty_data(self):
        """Slot to refresh faculty data."""
        logger.info("Refreshing faculty data...")
        if self.faculty_model.load_data(self.db_client):
            self.faculty_table_view.resizeColumnsToContents()
            self.faculty_table_view.setColumnHidden(0, True)
        else:
            logger.warning("Faculty data load failed or returned no data.")

    def _add_faculty(self):
        """Slot to open the Add Faculty dialog."""
        logger.info("Add Faculty button clicked.")
        if not self.db_client or self.db_client.is_offline():
            QMessageBox.warning(self, "Offline", "Database client not available. Cannot add faculty.")
            return

        dialog = FacultyDialog(parent=self)
        if dialog.exec():
            new_data = dialog.get_data()
            if new_data:
                logger.info(f"Attempting to add faculty: {new_data}")
                try:
                    new_id = self.db_client.add_faculty(None, new_data) # ID is auto-generated
                    if new_id:
                        logger.info(f"Faculty added successfully with ID: {new_id}")
                        QMessageBox.information(self, "Success", "Faculty member added successfully.")
                        self._refresh_faculty_data()
                    else:
                        logger.error("Failed to add faculty (db_client returned None).")
                        QMessageBox.critical(self, "Error", "Failed to add faculty member to the database.")
                except Exception as e:
                    logger.exception(f"Error adding faculty: {e}")
                    QMessageBox.critical(self, "Error", f"An error occurred while adding faculty:\n{e}")

    def _edit_faculty(self):
        """Slot to open the Edit Faculty dialog for the selected row."""
        logger.info("Edit Faculty button clicked.")
        if not self.db_client or self.db_client.is_offline():
            QMessageBox.warning(self, "Offline", "Database client not available. Cannot edit faculty.")
            return

        selected_indexes = self.faculty_table_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select a faculty member to edit.")
            return

        selected_row = selected_indexes[0].row()
        faculty_to_edit = self.faculty_model.get_faculty_by_row(selected_row)

        if not faculty_to_edit:
             QMessageBox.critical(self, "Error", "Could not retrieve data for the selected faculty.")
             return

        faculty_id = faculty_to_edit.get('id')
        if not faculty_id:
            QMessageBox.critical(self, "Error", "Could not determine the ID of the selected faculty.")
            return

        dialog = FacultyDialog(faculty_data=faculty_to_edit, parent=self)
        if dialog.exec():
            updated_data = dialog.get_data()
            if updated_data:
                logger.info(f"Attempting to update faculty (ID: {faculty_id}): {updated_data}")
                try:
                    update_payload = {k: v for k, v in updated_data.items() if k != 'id'}
                    success = self.db_client.update_faculty(faculty_id, update_payload)
                    if success:
                        logger.info(f"Faculty updated successfully: {faculty_id}")
                        QMessageBox.information(self, "Success", "Faculty member updated successfully.")
                        self._refresh_faculty_data()
                    else:
                        logger.error(f"Failed to update faculty (db_client returned False): {faculty_id}")
                        QMessageBox.critical(self, "Error", "Failed to update faculty member in the database.")
                except Exception as e:
                    logger.exception(f"Error updating faculty: {e}")
                    QMessageBox.critical(self, "Error", f"An error occurred while updating faculty:\n{e}")

    def _delete_faculty(self):
        """Slot to delete the selected faculty member."""
        logger.info("Delete Faculty button clicked.")
        if not self.db_client or self.db_client.is_offline():
            QMessageBox.warning(self, "Offline", "Database client not available. Cannot delete faculty.")
            return

        selected_indexes = self.faculty_table_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select a faculty member to delete.")
            return

        selected_row = selected_indexes[0].row()
        faculty_to_delete = self.faculty_model.get_faculty_by_row(selected_row)

        if not faculty_to_delete:
             QMessageBox.critical(self, "Error", "Could not retrieve data for the selected faculty.")
             return

        faculty_id = faculty_to_delete.get('id')
        faculty_name = faculty_to_delete.get('name', 'N/A')
        if not faculty_id:
            QMessageBox.critical(self, "Error", "Could not determine the ID of the selected faculty.")
            return

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete faculty member '{faculty_name}' (ID: {faculty_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Attempting to delete faculty (ID: {faculty_id})")
            try:
                success = self.db_client.delete_faculty(faculty_id)
                if success:
                    logger.info(f"Faculty deleted successfully: {faculty_id}")
                    QMessageBox.information(self, "Success", "Faculty member deleted successfully.")
                    self._refresh_faculty_data()
                else:
                    logger.error(f"Failed to delete faculty (db_client returned False): {faculty_id}")
                    QMessageBox.critical(self, "Error", "Failed to delete faculty member from the database.")
            except Exception as e:
                logger.exception(f"Error deleting faculty: {e}")
                QMessageBox.critical(self, "Error", f"An error occurred while deleting faculty:\n{e}")


    # --- Student Action Slots (NEW) ---

    def _refresh_students(self):
        """Slot to refresh student data."""
        logger.info("Refreshing student data...")
        if self.student_model.load_data(self.db_client):
            self.student_table_view.resizeColumnsToContents()
            self.student_table_view.setColumnHidden(0, True) # Hide Firestore ID
        else:
            logger.warning("Student data load failed or returned no data.")

    def _add_student(self):
        """Slot to open the Add Student dialog."""
        logger.info("Add Student button clicked.")
        if not self.db_client or self.db_client.is_offline():
            QMessageBox.warning(self, "Offline", "Database client not available. Cannot add student.")
            return

        dialog = StudentDialog(parent=self)
        if dialog.exec():
            new_data = dialog.get_data()
            if new_data:
                logger.info(f"Attempting to add student: {new_data}")
                try:
                    # *** Use the correct Firebase client method ***
                    new_id = self.db_client.add_student(None, new_data) # ID is auto-generated
                    if new_id:
                        logger.info(f"Student added successfully with ID: {new_id}")
                        QMessageBox.information(self, "Success", "Student added successfully.")
                        self._refresh_students() # Refresh student table
                    else:
                        logger.error("Failed to add student (db_client returned None).")
                        QMessageBox.critical(self, "Error", "Failed to add student to the database.")
                except Exception as e:
                    logger.exception(f"Error adding student: {e}")
                    QMessageBox.critical(self, "Error", f"An error occurred while adding student:\n{e}")

    def _edit_student(self):
        """Slot to open the Edit Student dialog for the selected row."""
        logger.info("Edit Student button clicked.")
        if not self.db_client or self.db_client.is_offline():
            QMessageBox.warning(self, "Offline", "Database client not available. Cannot edit student.")
            return

        selected_indexes = self.student_table_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select a student to edit.")
            return

        selected_row = selected_indexes[0].row()
        student_to_edit = self.student_model.get_student_by_row(selected_row)

        if not student_to_edit:
             QMessageBox.critical(self, "Error", "Could not retrieve data for the selected student.")
             return

        student_doc_id = student_to_edit.get('id') # Firestore document ID
        if not student_doc_id:
            QMessageBox.critical(self, "Error", "Could not determine the document ID of the selected student.")
            return

        dialog = StudentDialog(student_data=student_to_edit, parent=self)
        if dialog.exec():
            updated_data = dialog.get_data()
            if updated_data:
                logger.info(f"Attempting to update student (Doc ID: {student_doc_id}): {updated_data}")
                try:
                    # Remove 'id' if present in updated_data, as it's the document ID
                    update_payload = {k: v for k, v in updated_data.items() if k != 'id'}
                    # *** Use the correct Firebase client method ***
                    success = self.db_client.update_student(student_doc_id, update_payload)
                    if success:
                        logger.info(f"Student updated successfully: {student_doc_id}")
                        QMessageBox.information(self, "Success", "Student updated successfully.")
                        self._refresh_students() # Refresh student table
                    else:
                        logger.error(f"Failed to update student (db_client returned False): {student_doc_id}")
                        QMessageBox.critical(self, "Error", "Failed to update student in the database.")
                except Exception as e:
                    logger.exception(f"Error updating student: {e}")
                    QMessageBox.critical(self, "Error", f"An error occurred while updating student:\n{e}")

    def _delete_student(self):
        """Slot to delete the selected student."""
        logger.info("Delete Student button clicked.")
        if not self.db_client or self.db_client.is_offline():
            QMessageBox.warning(self, "Offline", "Database client not available. Cannot delete student.")
            return

        selected_indexes = self.student_table_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select a student to delete.")
            return

        selected_row = selected_indexes[0].row()
        student_to_delete = self.student_model.get_student_by_row(selected_row)

        if not student_to_delete:
             QMessageBox.critical(self, "Error", "Could not retrieve data for the selected student.")
             return

        student_doc_id = student_to_delete.get('id') # Firestore document ID
        student_name = student_to_delete.get('name', 'N/A')
        if not student_doc_id:
            QMessageBox.critical(self, "Error", "Could not determine the document ID of the selected student.")
            return

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete student '{student_name}' (Doc ID: {student_doc_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Attempting to delete student (Doc ID: {student_doc_id})")
            try:
                # *** Use the correct Firebase client method ***
                success = self.db_client.delete_student(student_doc_id)
                if success:
                    logger.info(f"Student deleted successfully: {student_doc_id}")
                    QMessageBox.information(self, "Success", "Student deleted successfully.")
                    self._refresh_students() # Refresh student table
                else:
                    logger.error(f"Failed to delete student (db_client returned False): {student_doc_id}")
                    QMessageBox.critical(self, "Error", "Failed to delete student from the database.")
            except Exception as e:
                logger.exception(f"Error deleting student: {e}")
                QMessageBox.critical(self, "Error", f"An error occurred while deleting student:\n{e}")


# ==============================================================================
# Example Usage (for testing)
# ==============================================================================
if __name__ == '__main__':
    import sys
    # Mock FirebaseClient for testing UI without real database interaction
    class MockFirebaseClient:
        def is_offline(self): return False
        def get_all_faculty(self):
            logger.info("MOCK: Getting all faculty")
            return [
                {'id': 'f1', 'name': 'Dr. Ada Lovelace', 'department': 'Computer Science', 'contact': 'ada@example.com', 'rfid_tag': 'F001', 'status': 'Active'},
                {'id': 'f2', 'name': 'Dr. Charles Babbage', 'department': 'Mathematics', 'contact': 'charles@example.com', 'rfid_tag': 'F002', 'status': 'Active'}
            ]
        def add_faculty(self, doc_id, data): logger.info(f"MOCK: Adding faculty: {data}"); return "new_faculty_id"
        def update_faculty(self, doc_id, data): logger.info(f"MOCK: Updating faculty {doc_id}: {data}"); return True
        def delete_faculty(self, doc_id): logger.info(f"MOCK: Deleting faculty {doc_id}"); return True

        def get_all_students(self):
            logger.info("MOCK: Getting all students")
            return [
                {'id': 's1', 'student_id': 'S1001', 'name': 'Alice Wonderland', 'rfid_tag': 'A001'},
                {'id': 's2', 'student_id': 'S1002', 'name': 'Bob The Builder', 'rfid_tag': 'B001'}
            ]
        def add_student(self, doc_id, data): logger.info(f"MOCK: Adding student: {data}"); return "new_student_id"
        def update_student(self, doc_id, data): logger.info(f"MOCK: Updating student {doc_id}: {data}"); return True
        def delete_student(self, doc_id): logger.info(f"MOCK: Deleting student {doc_id}"); return True

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    app = QApplication(sys.argv)
    mock_db = MockFirebaseClient()
    admin_panel = AdminPanel(db_client=mock_db)
    admin_panel.show()
    sys.exit(app.exec())