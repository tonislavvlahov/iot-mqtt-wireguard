# Защитена разпределена IoT система — MQTT & WireGuard VPN

Лабораторен проект по **Сигурност в кибер-физични системи**.  
Симулация на разпределена IoT архитектура с два възела, комуникиращи през криптиран WireGuard VPN тунел чрез протокол MQTT.

---

## Топология

```
┌─────────────────────────┐          WireGuard VPN          ┌─────────────────────────┐
│     СТРАНА А (10.0.0.1) │◄───────────────────────────────►│     СТРАНА Б (10.0.0.2) │
│   Климатичен контрол    │        Криптиран тунел           │      Хидро контрол      │
│                         │                                  │                         │
│  Сензор: Температура    │──── home/nodeA/temp ────────────►│  Актуатор: Температура  │
│  Актуатор: Влажност    │◄─── home/nodeB/humidity ──────────│  Сензор: Влажност       │
│                         │                                  │                         │
│  MQTT Broker (1883)     │◄──── MQTT Bridge ───────────────►│  MQTT Broker (1883)     │
└─────────────────────────┘                                  └─────────────────────────┘
```

---

## Функционалност

### Страна А — Климатичен контрол (`node_a.py`)
- **Виртуален сензор за температура** — генерира стойности между 15°C и 30°C с циклична промяна (60 сек. покачване / 60 сек. спадане)
- **Публикува** към `home/nodeA/temp` на брокера на Страна Б
- **Актуатор за влажност** — абониран за `home/nodeB/humidity`:
  - При влажност > 70% → `Включвам влагоабсорбатор`
  - При влажност < 40% → `Включвам овлажнител`

### Страна Б — Хидро контрол (`node_b.py`)
- **Виртуален сензор за влажност** — генерира стойности между 30% и 90%
- **Публикува** към `home/nodeB/humidity` на брокера на Страна А
- **Актуатор за температура** — абониран за `home/nodeA/temp`:
  - При температура > 25°C → `Включвам охлаждане`
  - При температура < 18°C → `Включвам отопление`

---

## Технологии

| Компонент | Технология |
|-----------|-----------|
| VPN тунел | WireGuard |
| MQTT Broker | Eclipse Mosquitto 2.x |
| Скриптове | Python 3 + paho-mqtt |
| Формат на съобщенията | JSON |
| Сигурност | Username/Password автентикация + WireGuard криптиране |

---

## Структура на съобщенията (JSON)

Всички съобщения са в структуриран JSON формат:

```json
{
  "value": 23.5,
  "unit": "°C",
  "timestamp": "2026-04-15T14:23:01.123456"
}
```

```json
{
  "value": 67.3,
  "unit": "%",
  "timestamp": "2026-04-15T14:23:01.123456"
}
```

---

## Бонус функции

- ✅ **JSON формат** — всяко съобщение съдържа стойност, мерна единица и времево клеймо
- ✅ **LWT (Last Will and Testament)** — при прекъсване се публикува автоматично на `home/nodeA/status` / `home/nodeB/status`
- ✅ **MQTT Bridge** — автоматична синхронизация на топици между двата брокера

---

## Инсталация и настройка

### Изисквания
- Windows 10/11
- Python 3.x
- [WireGuard за Windows](https://www.wireguard.com/install/)
- [Eclipse Mosquitto](https://mosquitto.org/download/)

### 1. WireGuard VPN

**Страна А** (`10.0.0.1`):
```ini
[Interface]
PrivateKey = <private key на Страна А>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <public key на Страна Б>
AllowedIPs = 10.0.0.2/32
Endpoint = <реален IP на Страна Б>:51820
PersistentKeepalive = 25
```

**Страна Б** (`10.0.0.2`):
```ini
[Interface]
PrivateKey = <private key на Страна Б>
Address = 10.0.0.2/24
ListenPort = 51820

[Peer]
PublicKey = <public key на Страна А>
AllowedIPs = 10.0.0.1/32
Endpoint = <реален IP на Страна А>:51820
PersistentKeepalive = 25
```

Тест на тунела:
```cmd
ping 10.0.0.1
```

### 2. Mosquitto MQTT Broker

Копирай `mosquitto_a.conf` или `mosquitto_b.conf` в `C:\Program Files\mosquitto\mosquitto.conf`.

Създай парола:
```cmd
cd "C:\Program Files\mosquitto"
mosquitto_passwd -c passwd.txt mqttuser
```

Стартирай брокера:
```cmd
mosquitto -c mosquitto.conf -v
```

Firewall правило:
```cmd
netsh advfirewall firewall add rule name="MQTT" dir=in action=allow protocol=TCP localport=1883
netsh advfirewall firewall add rule name="WireGuard" dir=in action=allow protocol=UDP localport=51820
```

### 3. Python скриптове

Инсталирай зависимостта:
```cmd
pip install paho-mqtt
```

Стартирай (всяка страна своя скрипт):
```cmd
python node_a.py   # Страна А
python node_b.py   # Страна Б
```

---

## Валидация

### Проверка на VPN тунела
```cmd
ping 10.0.0.1
```
В WireGuard приложението трябва да се вижда активен **Last handshake**.

### Проверка на MQTT потока
```cmd
mosquitto_sub -h 10.0.0.1 -p 1883 -u mqttuser -P mqtt1234 -t "home/#" -v
```

Или използвай [MQTT Explorer](https://mqtt-explorer.com/) за визуална проверка на топиците.

---

## Автори

Проект реализиран в екип от двама студенти като част от курс **Сигурност в кибер-физични системи**.
