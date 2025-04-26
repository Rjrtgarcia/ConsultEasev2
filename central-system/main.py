# central-system/main.py
"""
Main entry point for the ConsultEase Central System application.
Initializes the PyQt application and displays the main window.
"""
import sys
import logging
from PyQt6.QtWidgets import QApplication # Changed from PyQt5
import os # For MQTT config path

# Adjust the path to import from the ui directory if necessary,
# depending on how you run the script.
# If running from the root 'ConsultEase' directory:
from central_system.ui.main_window import MainWindow
from central_system.database.firebase_client import FirebaseClient, FIREBASE_AVAILABLE
from central_system.comms.mqtt_client import MQTTClient, MQTT_AVAILABLE
# If running directly from 'central-system' directory, you might need:
# from ui.main_window import MainWindow
# from database.firebase_client import FirebaseClient
# from comms.mqtt_client import MQTTClient

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Initializes and runs the PyQt application.
    """
    try:
        logging.info("Starting ConsultEase Central System...")
# Set input method module for Wayland/squeekboard integration
        os.environ['QT_IM_MODULE'] = 'wayland'
        app = QApplication(sys.argv)

        # --- Firebase Initialization ---
        firebase_client = None
        if FIREBASE_AVAILABLE:
            try:
                # Assumes serviceAccountKey.json is findable by the client
                firebase_client = FirebaseClient()
                logging.info("FirebaseClient initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to initialize FirebaseClient: {e}. Proceeding without Firebase integration.")
        else:
            logging.warning("Firebase libraries not installed. Proceeding without Firebase integration.")

        # --- MQTT Initialization ---
        mqtt_client = None
        if MQTT_AVAILABLE:
            try:
                # Construct path relative to this script's location or project root
                # Assuming main.py is in central-system/
                config_path = os.path.join(os.path.dirname(__file__), '..', 'faculty-unit', 'config', 'config.h')
                # A more robust way might be needed if structure changes
                # Or pass absolute path or use environment variables
                mqtt_client = MQTTClient(config_path=config_path) # Pass config path
                logging.info("MQTTClient initialized.")
                # Note: Connection is usually initiated later, e.g., in the UI component that needs it.
            except Exception as e:
                logging.error(f"Failed to initialize MQTTClient: {e}. Proceeding without MQTT integration.")
        else:
            logging.warning("Paho MQTT library not installed. Proceeding without MQTT integration.")


        # --- Apply Stylesheet ---
        style_path = os.path.join(os.path.dirname(__file__), 'ui', 'styles.qss')
        if os.path.exists(style_path):
            try:
                with open(style_path, 'r') as f:
                    app.setStyleSheet(f.read())
                logging.info(f"Successfully loaded stylesheet from: {style_path}")
            except Exception as e:
                logging.error(f"Error loading stylesheet from {style_path}: {e}")
        else:
            logging.warning(f"Stylesheet not found at: {style_path}. Using default style.")


        # Pass the clients (which might be None) to MainWindow
        main_window = MainWindow(firebase_client=firebase_client, mqtt_client=mqtt_client)
        main_window.show()
        logging.info("Main window displayed.")

        sys.exit(app.exec_())

    except ImportError as e:
        logging.error(f"Failed to import necessary modules: {e}")
        print(f"Import Error: {e}. Make sure PyQt6 is installed and the module paths are correct.", file=sys.stderr) # Changed from PyQt5
        sys.exit(1)
    except Exception as e:
        logging.exception("An unexpected error occurred:") # Logs the full traceback
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()