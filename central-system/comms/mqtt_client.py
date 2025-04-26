import paho.mqtt.client as mqtt
from PyQt6.QtCore import QObject, pyqtSignal
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MQTTClient(QObject):
    """
    A basic MQTT client integrated with PyQt6 signals for asynchronous communication.
    """
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    message_received = pyqtSignal(str, str)  # topic, payload

    def __init__(self, broker_address, port=1883, client_id="", parent=None):
        """
        Initializes the MQTTClient.

        Args:
            broker_address (str): The address of the MQTT broker.
            port (int): The port of the MQTT broker (default: 1883).
            client_id (str): The client ID to use for the connection (default: "").
            parent (QObject): The parent QObject (default: None).
        """
        super().__init__(parent)
        self.broker_address = broker_address
        self.port = port
        self.client_id = client_id

        # Using MQTTv3.1.1 as specified, could use MQTTv5 if needed later
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)

        # Assign internal callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        logger.info(f"MQTTClient initialized for broker {broker_address}:{port}")

    def connect_to_broker(self):
        """
        Connects to the MQTT broker asynchronously and starts the network loop.
        """
        try:
            logger.info(f"Attempting to connect to MQTT broker at {self.broker_address}:{self.port}...")
            self.client.connect_async(self.broker_address, self.port, 60)
            self.client.loop_start()  # Start network loop in a separate thread
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")

    def disconnect_from_broker(self):
        """
        Stops the network loop and disconnects from the MQTT broker.
        """
        logger.info("Disconnecting from MQTT broker...")
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")

    def publish(self, topic, payload, qos=1, retain=False):
        """
        Publishes a message to a specific topic.

        Args:
            topic (str): The topic to publish to.
            payload (str): The message payload.
            qos (int): The Quality of Service level (0, 1, or 2) (default: 1).
            retain (bool): Whether the message should be retained (default: False).
        """
        logger.info(f"Publishing to topic '{topic}': {payload[:50]}{'...' if len(payload) > 50 else ''}")
        result, mid = self.client.publish(topic, payload, qos, retain)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.warning(f"Failed to publish message to topic '{topic}'. Result code: {result}")
        return result, mid

    def subscribe(self, topic, qos=1):
        """
        Subscribes to a specific topic.

        Args:
            topic (str): The topic to subscribe to.
            qos (int): The desired Quality of Service level (default: 1).
        """
        logger.info(f"Subscribing to topic '{topic}' with QoS {qos}")
        result, mid = self.client.subscribe(topic, qos)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.warning(f"Failed to subscribe to topic '{topic}'. Result code: {result}")
        return result, mid

    def _on_connect(self, client, userdata, flags, rc):
        """
        Internal callback triggered when the client connects to the broker.
        """
        if rc == 0:
            logger.info("Successfully connected to MQTT broker.")
            self.connected.emit()
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            # Optionally emit a specific error signal or handle reconnection logic here later

    def _on_disconnect(self, client, userdata, rc):
        """
        Internal callback triggered when the client disconnects from the broker.
        """
        logger.info(f"Disconnected from MQTT broker. Return code: {rc}")
        self.disconnected.emit()
        # Note: rc != 0 often indicates an unexpected disconnect.
        # Reconnection logic could be added here if needed.

    def _on_message(self, client, userdata, msg):
        """
        Internal callback triggered when a message is received.
        """
        try:
            payload = msg.payload.decode('utf-8')
            logger.info(f"Received message on topic '{msg.topic}': {payload[:50]}{'...' if len(payload) > 50 else ''}")
            self.message_received.emit(msg.topic, payload)
        except UnicodeDecodeError:
            logger.warning(f"Received message on topic '{msg.topic}' with non-UTF-8 payload.")
        except Exception as e:
            logger.error(f"Error processing received message: {e}")

# Example usage (for testing purposes, remove or comment out in production)
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit
    from PyQt6.QtCore import QTimer

    class TestWidget(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("MQTT Client Test")
            self.layout = QVBoxLayout(self)
            self.log_area = QTextEdit()
            self.log_area.setReadOnly(True)
            self.connect_button = QPushButton("Connect")
            self.disconnect_button = QPushButton("Disconnect")
            self.publish_button = QPushButton("Publish Test Message")
            self.subscribe_button = QPushButton("Subscribe to 'test/topic'")

            self.layout.addWidget(self.log_area)
            self.layout.addWidget(self.connect_button)
            self.layout.addWidget(self.disconnect_button)
            self.layout.addWidget(self.subscribe_button)
            self.layout.addWidget(self.publish_button)

            # --- MQTT Client Setup ---
            # Replace with your broker details if needed
            # Using a public test broker for this example
            broker = "mqtt.eclipseprojects.io"
            port = 1883
            self.mqtt_client = MQTTClient(broker_address=broker, port=port, client_id="PyQtTestClient_MidLevel")

            # --- Connect Signals ---
            self.connect_button.clicked.connect(self.mqtt_client.connect_to_broker)
            self.disconnect_button.clicked.connect(self.mqtt_client.disconnect_from_broker)
            self.publish_button.clicked.connect(self.publish_message)
            self.subscribe_button.clicked.connect(self.subscribe_topic)

            self.mqtt_client.connected.connect(self.on_mqtt_connected)
            self.mqtt_client.disconnected.connect(self.on_mqtt_disconnected)
            self.mqtt_client.message_received.connect(self.on_mqtt_message_received)

            self.disconnect_button.setEnabled(False)
            self.publish_button.setEnabled(False)
            self.subscribe_button.setEnabled(False)

            self.log_message(f"MQTT Client Initialized for {broker}:{port}")

        def publish_message(self):
            topic = "test/topic/pyqt"
            message = f"Hello from PyQt Client! Time: {QTimer.singleShot(0, lambda: None)}" # Simple way to get a changing value
            self.mqtt_client.publish(topic, message)
            self.log_message(f"Published to {topic}: {message}")

        def subscribe_topic(self):
            topic = "test/topic/#" # Subscribe to a wildcard topic
            self.mqtt_client.subscribe(topic)
            self.log_message(f"Subscribed to {topic}")
            self.subscribe_button.setEnabled(False) # Disable after subscribing once

        def on_mqtt_connected(self):
            self.log_message("MQTT Connected!")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.publish_button.setEnabled(True)
            self.subscribe_button.setEnabled(True)

        def on_mqtt_disconnected(self):
            self.log_message("MQTT Disconnected!")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.publish_button.setEnabled(False)
            self.subscribe_button.setEnabled(False) # Re-enable connect to allow re-subscribing

        def on_mqtt_message_received(self, topic, payload):
            self.log_message(f"Received on '{topic}': {payload}")

        def log_message(self, message):
            self.log_area.append(message)
            logger.info(message) # Also log to console via logger

        def closeEvent(self, event):
            # Ensure disconnection on close
            self.mqtt_client.disconnect_from_broker()
            super().closeEvent(event)

    app = QApplication(sys.argv)
    widget = TestWidget()
    widget.show()
    sys.exit(app.exec())