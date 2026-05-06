# Secured Distributed IoT System — MQTT & WireGuard VPN
  
Simulates a distributed IoT architecture with two nodes communicating over an encrypted WireGuard VPN tunnel using the MQTT protocol.

---

## Overview

Two isolated nodes exchange sensor data over a secure VPN tunnel. Each node runs its own MQTT broker and a Python script that simulates sensors and actuators reacting to incoming data.

---

## Topology

| | Node A (10.0.0.1) | | Node B (10.0.0.2) |
|---|---|---|---|
| Sensor | Temperature | →→→ | Actuator: Temperature |
| Actuator | Humidity | ←←← | Sensor: Humidity |

> Both nodes communicate over an encrypted **WireGuard VPN tunnel** via **MQTT Bridge**.

## How It Works

**Node A — Climate Control** (`node_a.py`)
- Generates temperature values between 15°C and 30°C
- Publishes to `home/nodeA/temp` on Node B's broker
- Subscribes to `home/nodeB/humidity`:
  - Humidity > 70% → activates dehumidifier
  - Humidity < 40% → activates humidifier

**Node B — Hydro Control** (`node_b.py`)
- Generates humidity values between 30% and 90%
- Publishes to `home/nodeB/humidity` on Node A's broker
- Subscribes to `home/nodeA/temp`:
  - Temperature > 25°C → activates cooling
  - Temperature < 18°C → activates heating

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| VPN Tunnel | WireGuard |
| MQTT Broker | Eclipse Mosquitto 2.x |
| Scripts | Python 3 + paho-mqtt |
| Message Format | JSON |
| Security | Username/Password + WireGuard encryption |

---

## Message Format

```json
{
  "value": 23.5,
  "unit": "°C",
  "timestamp": "2026-04-15T14:23:01.123456"
}
```

---

## Features

- Encrypted communication over WireGuard VPN
- Bidirectional MQTT bridge between two brokers
- JSON structured messages with timestamps
- LWT (Last Will and Testament) on disconnect
- Username/password authentication on both brokers

---

## Getting Started

### Requirements
- Windows 10/11
- Python 3.x
- [WireGuard](https://www.wireguard.com/install/)
- [Eclipse Mosquitto](https://mosquitto.org/download/)

### 1. Install dependencies
```cmd
pip install paho-mqtt
```

### 2. Configure Mosquitto
Copy the provided config file to `C:\Program Files\mosquitto\mosquitto.conf` and create a password file:
```cmd
cd "C:\Program Files\mosquitto"
mosquitto_passwd -c passwd.txt mqttuser
mosquitto -c mosquitto.conf -v
```

### 3. Run
```cmd
python node_a.py   # on Node A
python node_b.py   # on Node B
```

---

## Validation

Check VPN tunnel:
```cmd
ping 10.0.0.1
```

Monitor MQTT messages:
```cmd
mosquitto_sub -h 10.0.0.1 -p 1883 -u mqttuser -P mqtt1234 -t "home/#" -v
```

Or use [MQTT Explorer](https://mqtt-explorer.com/) for a visual overview.

---
