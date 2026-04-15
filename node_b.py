import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# ===================== КОНФИГУРАЦИЯ =====================
# Брокерът на Страна А (където публикуваме влажността)
BROKER_A_HOST = "10.0.0.1"   # VPN IP на Страна А
BROKER_A_PORT = 1883
BROKER_A_USER = "mqttuser"
BROKER_A_PASS = "mqtt1234"   # Паролата на Страна А

# Брокерът на Страна Б (където се абонираме за температура)
BROKER_B_HOST = "10.0.0.2"   # Собственият ни VPN IP
BROKER_B_PORT = 1883
BROKER_B_USER = "mqttuser"
BROKER_B_PASS = "mqtt1234"   # Нашата собствена парола

TOPIC_PUBLISH   = "home/nodeB/humidity"
TOPIC_SUBSCRIBE = "home/nodeA/temp"

# ===================== АКТУАТОР (абонат) =====================
def on_connect_sub(client, userdata, flags, rc):
    if rc == 0:
        print("[Актуатор Б] Свързан с брокера на Страна Б")
        client.subscribe(TOPIC_SUBSCRIBE)
        print(f"[Актуатор Б] Абониран за: {TOPIC_SUBSCRIBE}")
    else:
        print(f"[Актуатор Б] Грешка при свързване: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload.get("value", 0)
        unit = payload.get("unit", "°C")
        ts   = payload.get("timestamp", "")
        print(f"\n[Актуатор Б] Получена температура: {temp}{unit} @ {ts}")

        if temp > 25:
            print("[Актуатор Б] >>> Включвам охлаждане <<<")
        elif temp < 18:
            print("[Актуатор Б] >>> Включвам отопление <<<")
        else:
            print("[Актуатор Б]     Температурата е в норма — без действие")
    except Exception as e:
        print(f"[Актуатор Б] Грешка при парсване: {e}")

# ===================== СЕНЗОР (публикатор) =====================
# Глобалната стойност на влажността се променя плавно
_current_humidity = 60.0
_direction = 1  # 1 = расте, -1 = пада

def generate_humidity():
    """Генерира реалистична плавна влажност между 30% и 90%"""
    global _current_humidity, _direction
    change = random.uniform(0.5, 2.5) * _direction
    _current_humidity += change
    if _current_humidity >= 90:
        _current_humidity = 90.0
        _direction = -1
    elif _current_humidity <= 30:
        _current_humidity = 30.0
        _direction = 1
    return round(_current_humidity, 1)

def main():
    # --- Абонатен клиент (слуша температура от собствения ни брокер) ---
    sub_client = mqtt.Client(client_id="nodeB_actuator")
    sub_client.username_pw_set(BROKER_B_USER, BROKER_B_PASS)

    # LWT — Last Will and Testament
    sub_client.will_set(
        "home/nodeB/status",
        json.dumps({"status": "Node B Disconnected", "timestamp": datetime.now().isoformat()}),
        qos=1, retain=True
    )

    sub_client.on_connect = on_connect_sub
    sub_client.on_message = on_message

    try:
        sub_client.connect(BROKER_B_HOST, BROKER_B_PORT, 60)
        sub_client.loop_start()
    except Exception as e:
        print(f"[Актуатор Б] Не може да се свърже с локалния брокер: {e}")

    # --- Публикуващ клиент (изпраща влажност към брокера на A) ---
    pub_client = mqtt.Client(client_id="nodeB_sensor")
    pub_client.username_pw_set(BROKER_A_USER, BROKER_A_PASS)

    try:
        pub_client.connect(BROKER_A_HOST, BROKER_A_PORT, 60)
        pub_client.loop_start()
        print(f"[Сензор Б] Свързан с брокера на Страна А ({BROKER_A_HOST})")
    except Exception as e:
        print(f"[Сензор Б] Не може да се свърже с брокера на Страна А: {e}")
        return

    print("\n=== Страна Б: Хидро контрол — СТАРТИРАН ===")
    print(f"  Публикува влажност към: {BROKER_A_HOST} -> {TOPIC_PUBLISH}")
    print(f"  Слуша температура от: {BROKER_B_HOST} -> {TOPIC_SUBSCRIBE}\n")

    try:
        while True:
            humidity = generate_humidity()

            payload = json.dumps({
                "value": humidity,
                "unit": "%",
                "timestamp": datetime.now().isoformat()
            })

            result = pub_client.publish(TOPIC_PUBLISH, payload, qos=1)
            print(f"[Сензор Б] Публикувана влажност: {humidity}%  |  Топик: {TOPIC_PUBLISH}")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Страна Б] Спиране...")
    finally:
        pub_client.loop_stop()
        pub_client.disconnect()
        sub_client.loop_stop()
        sub_client.disconnect()
        print("[Страна Б] Изключен.")

if __name__ == "__main__":
    main()
