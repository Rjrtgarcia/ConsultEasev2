# central-system/ui/main_window.py
"""
This module defines the main window for the ConsultEase Central System UI.
"""
import sys
import logging # Add logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QDialog # Change to PyQt6 and add QDialog
from PyQt6.QtCore import Qt

# Import the new dialog and dashboard
from .auth_dialog import AuthDialog
from .faculty_dashboard import FacultyDashboard
from .admin_panel import AdminPanel # Import AdminPanel

logger = logging.getLogger(__name__) # Setup logger

class MainWindow(QMainWindow):
    """
    The main application window, inheriting from QMainWindow.
    This window will serve as the container for different views (Login, Dashboard, Admin).
    """
    def __init__(self, firebase_client=None, mqtt_client=None, parent=None): # Accept both clients
        """
        Initializes the MainWindow.
        Sets the window title, default size, and creates the basic layout
        with a placeholder label.
        """
        super().__init__(parent)

        self.firebase_client = firebase_client # Store the firebase client
        self.mqtt_client = mqtt_client         # Store the mqtt client
        self.setWindowTitle("ConsultEase Central System")
        # self.setGeometry(100, 100, 1000, 700) # x, y, width, height - Commented out for Kiosk Mode
        self.setWindowState(Qt.WindowState.WindowFullScreen) # Set to fullscreen for Kiosk Mode

        # --- Show Auth Dialog First ---
        # Pass firebase_client to AuthDialog
        auth_dialog = AuthDialog(firebase_client=self.firebase_client, parent=self)
        result = auth_dialog.exec() # Show modally

        # --- Load Content Based on Auth Result ---
        if result == QDialog.DialogCode.Accepted:
            # Retrieve authenticated student info
            authenticated_student_id = auth_dialog.get_authenticated_student_id()
            authenticated_student_name = auth_dialog.get_authenticated_student_name() # Optional, but good to have

            if authenticated_student_id:
                logger.info(f"Authentication successful for {authenticated_student_name} (ID: {authenticated_student_id}). Loading Faculty Dashboard.")
                # TODO: Implement role check to decide between AdminPanel and FacultyDashboard based on user role from AuthDialog
                # For now, directly load FacultyDashboard, passing the student ID
                faculty_dashboard = FacultyDashboard(
                    firebase_client=self.firebase_client,
                    mqtt_client=self.mqtt_client,
                    student_id=authenticated_student_id, # Pass the authenticated ID
                    parent=self
                )
                self.setCentralWidget(faculty_dashboard)
                logger.info("FacultyDashboard set as central widget.")
            else:
                # This case should ideally not happen if AuthDialog.accept() requires an ID, but handle defensively
                logger.error("Authentication dialog accepted, but no student ID was retrieved. Cannot load dashboard.")
                QMessageBox.critical(self, "Authentication Error", "Failed to retrieve student information after login.")
                # Close the application if we can't proceed
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, self.close)

            # --- Keep AdminPanel loading commented out for now ---
            # logger.info("TEMP: Loading AdminPanel instead of FacultyDashboard.")
            # admin_widget = AdminPanel(db_client=self.firebase_client, parent=self) # Pass client
            # self.setCentralWidget(admin_widget)
        else:
            logger.warning("Authentication failed or cancelled. Closing application.")
            # Close the main window immediately if auth fails
            # Need to delay the close slightly to allow the event loop to process
            # Otherwise, the window might not even appear before closing.
            # A more robust way might involve signals, but QTimer.singleShot is simple here.
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.close)

# Example usage for testing this window directly (optional)
if __name__ == '__main__':
    # Setup basic logging for the example
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    app = QApplication(sys.argv)
    mainWin = MainWindow()
    # The dialog runs in __init__, so we just need to show the window
    # if the dialog didn't cause an exit.
    # Check if the window is still valid before showing
    if mainWin.isVisible() or not mainWin.isHidden(): # A bit redundant, but safe
         mainWin.show()
         sys.exit(app.exec()) # Use exec() for PyQt6
    else:
         logger.info("Main window was likely closed during auth dialog.")
         sys.exit(0) # Exit cleanly if window closed early