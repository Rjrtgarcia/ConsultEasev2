# MQTT Communication Module

## Broker Configuration
```cpp
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient client(espClient);

void reconnect() {
  while (!client.connected()) {
    if (client.connect("FacultyUnit")) {
      client.subscribe("faculty/status");
    }
  }
}
```

## Message Protocol
| Topic               | Payload Format      |
|---------------------|---------------------|
| faculty/status      | JSON {id, present}  |
| requests/incoming   | CSV student_id,msg |

[QoS Settings...]