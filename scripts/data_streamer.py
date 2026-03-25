import pandas as pd
import requests
import time
import random
import os

# ==========================================
# CONFIGURATION
# ==========================================
API_URL = "http://127.0.0.1:8000/recommend"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "processed",
    "processed_data.csv"
)

DELAY_SECONDS = 4
SAMPLES_COUNT = 50
# ==========================================

def run_stream():
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Ошибка: Файл {DATASET_PATH} не найден.")
        return

    print(f"📡 Запуск Data Feeder...")
    print(f"🔗 API Endpoint: {API_URL}")
    print("Нажмите Ctrl+C для остановки.\n")
    
    df = pd.read_csv(DATASET_PATH)
    
    for _, row in df.sample(SAMPLES_COUNT).iterrows():
        features = row.drop("last_temp").to_dict()
        
        # Симуляция "середины" процесса (60-90% готовности)
        progress_factor = random.uniform(0.6, 0.9)
        features["total_arc_energy"] *= progress_factor
        features["total_heating_duration"] *= progress_factor
        
        # --- СТРОГИЙ ПЕРЕСЧЕТ ФИЗИКИ (Защита от рассинхрона и деления на ноль) ---
        if features["total_heating_duration"] > 0:
            features["energy_rate"] = features["total_arc_energy"] / features["total_heating_duration"]
            
            pf = features.get("mean_power_factor", 1.0)
            if pf == 0: pf = 1.0
            
            active_power = (features["total_arc_energy"] / features["total_heating_duration"]) * 1000
            features["mean_apparent_power"] = active_power / pf
        else:
            features["energy_rate"] = 0.0
            features["mean_apparent_power"] = 0.0
        # --------------------------------------------------------

        # Генерация реалистичной цели
        realistic_target = round(row["last_temp"] + random.uniform(-1.0, 2.0), 1)
        
        payload = {
            "target_temp": realistic_target,
            "features": features
        }
        
        try:
            response = requests.post(API_URL, json=payload)
            
            # Защита от HTTP-ошибок (400, 422, 500)
            if response.status_code != 200:
                detail = response.json().get("detail", f"HTTP {response.status_code}")
                print(f"❌ API Error: {detail}")
                continue
                
            result = response.json()
            
            status = result.get('status', 'error')
            delta = result.get('delta_energy', 0.0)
            pred = result.get('pred', 0.0)
            
            # Логика отображения статусов
            if status in ["optimal", "stable"]:
                status_symbol = "✅"
            elif status == "constraint_blocked":
                status_symbol = "🛑"
            else:
                status_symbol = "⚠️"
                
            print(f"{status_symbol} Target: {realistic_target:>6.1f}°C | "
                  f"Status: {status:<18} | "
                  f"ΔE: {delta:>6.1f} MJ | "
                  f"Pred: {pred:>6.1f}°C")
            
        except requests.exceptions.ConnectionError:
            print("❌ Ошибка: API сервер недоступен. Убедитесь, что uvicorn запущен.")
            break
        except Exception as e:
            print(f"⚠️ Неизвестная ошибка: {e}")
            
        time.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    run_stream()