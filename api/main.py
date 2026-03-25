from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.inference.simulate import simulate
from src.models.model_loader import load_model
from src.models.model_schema import EXPECTED_COLUMNS
from src.recommend.recommendation_engine import recommend

from src.reporting.stats_collector import stats_collector

# ⚠️ Аккуратно, проверь этот импорт. 
# Укажи правильный путь к твоему файлу publisher.py, если он лежит в другой папке.
from mqtt.publisher import publish


class PredictRequest(BaseModel):
    features: dict


class RecommendRequest(BaseModel):
    target_temp: float
    features: dict


app = FastAPI()
model = load_model()

try:
    if hasattr(model, "feature_names_") and model.feature_names_ is not None:
        if list(model.feature_names_) != EXPECTED_COLUMNS:
            raise Exception("Model feature names do not match EXPECTED_COLUMNS")
except Exception as e:
    raise Exception(f"Model schema mismatch: {e}")


@app.post("/predict")
def predict(request: PredictRequest):
    try:
        predicted_temp = simulate(model, request.features, EXPECTED_COLUMNS)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "predicted_temp": predicted_temp,
    }


@app.post("/recommend", summary="Подбор оптимального режима (ML + Физика)")
async def recommend_mode(request: RecommendRequest, background_tasks: BackgroundTasks):
    features_dict = request.features
    target = request.target_temp
    
    try:
        # 1. Расчет рекомендации
        result = recommend(model, features_dict, target, EXPECTED_COLUMNS)
        
        # 2. Обновление статистики (если расчет успешен)
        if result:
            stats_collector.update(result)
        
        # 3. Отправка в IoT через фоновую задачу
        background_tasks.add_task(
            publish,
            predicted=result["pred"],
            target=target,
            delta_energy=result["delta_energy"],
            status=result["status"],
            decision=result.get("decision", "unknown"),
            action=result.get("action", "unknown"),
            severity=result.get("severity", "normal"),
            message_text=result.get("message", ""),
            stats=stats_collector.to_dict()  # Передаем актуальный отчет
        )
            
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))