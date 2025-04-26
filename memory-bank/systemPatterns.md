# System Architecture Patterns
*Last updated: {{DATE}}*

## Component Diagram
```mermaid
graph LR
    A[RPi Central] --> B[Firebase]
    A --> C[MQTT Broker]
    C --> D[ESP32 Units]
    B --> C
```

## Event Flow
```mermaid
sequenceDiagram
    Student->>RPi: Scan RFID
    RPi->>Firebase: Write auth log
    Firebase->>MQTT: Publish availability
    MQTT->>ESP32: Update display
```

## Key Decisions
1. PyQt over Tkinter for touch support
2. MQTT over HTTP for real-time updates
3. Firebase Realtime Database for sync

## Failure Modes
- RFID reader timeout: Auto-retry 3x
- MQTT disconnect: Local cache + resync
- Firebase outage: Fallback to JSON storage

## Recovery Patterns
1. **Firebase Disconnect**:
   - Cache writes locally
   - Retry every 30s
   - Alert after 5 failures

2. **MQTT Broker Down**:
   - Use Firebase as message queue
   - Sync on reconnect

3. **Hardware Failures**:
   - Circuit breaker pattern for hardware comms
   - Graceful degradation for ESP32 units

// File version: 1.1-firebase
