import json
import time
import paho.mqtt.client as mqtt
import socket
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла один раз при старте
load_dotenv()

def publish(predicted, target, delta_energy, status, decision, action, severity, message_text, stats=None):
    try:
        # Защита от None и приведение к float
        predicted = float(predicted or 0.0)
        target = float(target or 0.0)
        delta_energy = float(delta_energy or 0.0)
    except (ValueError, TypeError):
        raise Exception("predicted, target, delta_energy must be numeric")

    # Формируем базовый пакет данных
    message = {
        "predicted": predicted,
        "target": target,
        "delta_energy": delta_energy,
        "status": status,
        "decision": decision,
        "action": action,
        "severity": severity,
        "message": message_text
    }

    # Если передана статистика, подмешиваем её в основной JSON
    if stats and isinstance(stats, dict):
        message.update(stats)

    payload = json.dumps(message)

    # Твои локальные настройки 
    broker = "localhost"
    port = 1883
    topic = "v1/devices/me/telemetry"
    # Читаем токен безопасно. Если .env нет, выдаст ошибку
    device_token = os.getenv("DEVICE_TOKEN")
    
    if not device_token:
        raise ValueError("DEVICE_TOKEN is not set in .env file")

    client = mqtt.Client()
    client.username_pw_set(device_token)

    try:
        print("MQTT: connecting...")
        rc = client.connect(broker, port, keepalive=60)
        
        if rc != 0:
            print(f"MQTT ERROR: Connection failed with code {rc}")
            return

        client.loop_start()
        time.sleep(0.5)

        print("MQTT SEND:", payload)
        result = client.publish(topic, payload, qos=0)
        # Оставляем твой таймаут, но помни, что 10с может блокировать поток при сбоях
        success = result.wait_for_publish(timeout=10)

        if success:
            print("MQTT SUCCESS: Data delivered and confirmed")
        else:
            print("MQTT WARNING: Message sent but NOT confirmed by broker (timeout)")

    except (socket.timeout, TimeoutError):
        print("MQTT ERROR: connection timeout")
    except Exception as e:
        print(f"MQTT ERROR: {e}")
    finally:
        try:
            time.sleep(0.2)
            client.loop_stop()
            client.disconnect()
            print("MQTT: disconnected")
        except Exception:
            pass