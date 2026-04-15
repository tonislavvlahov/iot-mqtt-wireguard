import paho.mqtt.client as mqtt
import json
import time
import math
from datetime import datetime

# ===================== КОНФИГУРАЦИЯ =====================
# Брокерът на Страна Б (където публикуваме температурата)
BROKER_B_HOST = "10.0.0.2"   # VPN IP на Страна Б
BROKER_B_PORT = 1883
BROKER_B_USER = "mqttuser"
BROKER_B_PASS = "mqtt1234"   # Паролата на Страна Б

# Брокерът на Страна А (където се абонираме за влажност)
BROKER_A_HOST = "10.0.0.1"   # Собственият ни VPN IP
BROKER_A_PORT = 1883
BROKER_A_USER = "mqttuser"
BROKER_A_PASS = "mqtt1234"   # Нашата собствена парола

TOPIC_PUBLISH   = "home/nodeA/temp"
TOPIC_SUBSCRIBE = "home/nodeB/humidity"

# ===================== АКТУАТОР (абонат) =====================
def on_connect_sub(client, userdata, flags, rc):
    if rc == 0:
        print("[Актуатор A] Свързан с брокера на Страна А")
        client.subscribe(TOPIC_SUBSCRIBE)
        print(f"[Актуатор A] Абониран за: {TOPIC_SUBSCRIBE}")
    else:
        print(f"[Актуатор A] Грешка при свързване: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        humidity = payload.get("value", 0)
        unit     = payload.get("unit", "%")
        ts       = payload.get("timestamp", "")
        print(f"\n[Актуатор A] Получена влажност: {humidity}{unit} @ {ts}")

        if humidity > 70:
            print("[Актуатор A] >>> Включвам влагоабсорбатор <<<")
        elif humidity < 40:
            print("[Актуатор A] >>> Включвам овлажнител <<<")
        else:
            print("[Актуатор A]     Влажността е в норма — без действие")
    except Exception as e:
        print(f"[Актуатор A] Грешка при парсване: {e}")

# ===================== СЕНЗОР (публикатор) =====================
def generate_temperature(elapsed_seconds):
    """Циклична промяна: 60с покачване (15→30°C), 60с спадане (30→15°C)"""
    cycle = elapsed_seconds % 120
    if cycle < 60:
        progress = cycle / 60.0
    else:
        progress = (120 - cycle) / 60.0
    return round(15 + progress * 15, 2)

def main():
    # --- Абонатен клиент (слуша влажност от брокера на A) ---
    sub_client = mqtt.Client(client_id="nodeA_actuator")
    sub_client.username_pw_set(BROKER_A_USER, BROKER_A_PASS)

    # LWT — Last Will and Testament
    sub_client.will_set(
        "home/nodeA/status",
        json.dumps({"status": "Node A Disconnected", "timestamp": datetime.now().isoformat()}),
        qos=1, retain=True
    )

    sub_client.on_connect = on_connect_sub
    sub_client.on_message = on_message

    try:
        sub_client.connect(BROKER_A_HOST, BROKER_A_PORT, 60)
        sub_client.loop_start()
    except Exception as e:
        print(f"[Актуатор A] Не може да се свърже с локалния брокер: {e}")

    # --- Публикуващ клиент (изпраща температура към брокера на B) ---
    pub_client = mqtt.Client(client_id="nodeA_sensor")
    pub_client.username_pw_set(BROKER_B_USER, BROKER_B_PASS)

    try:
        pub_client.connect(BROKER_B_HOST, BROKER_B_PORT, 60)
        pub_client.loop_start()
        print(f"[Сензор A] Свързан с брокера на Страна Б ({BROKER_B_HOST})")
    except Exception as e:
        print(f"[Сензор A] Не може да се свърже с брокера на Страна Б: {e}")
        return

    print("\n=== Страна А: Климатичен контрол — СТАРТИРАН ===")
    print(f"  Публикува температура към: {BROKER_B_HOST} -> {TOPIC_PUBLISH}")
    print(f"  Слуша влажност от: {BROKER_A_HOST} -> {TOPIC_SUBSCRIBE}\n")

    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time
            temp = generate_temperature(elapsed)

            payload = json.dumps({
                "value": temp,
                "unit": "°C",
                "timestamp": datetime.now().isoformat()
            })

            result = pub_client.publish(TOPIC_PUBLISH, payload, qos=1)
            print(f"[Сензор A] Публикувана температура: {temp}°C  |  Топик: {TOPIC_PUBLISH}")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Страна А] Спиране...")
    finally:
        pub_client.loop_stop()
        pub_client.disconnect()
        sub_client.loop_stop()
        sub_client.disconnect()
        print("[Страна А] Изключен.")

if __name__ == "__main__":
    main()
