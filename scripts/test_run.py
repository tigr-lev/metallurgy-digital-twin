import sys
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.inference.simulate import simulate
from src.models.model_loader import load_model
from src.models.model_schema import EXPECTED_COLUMNS
from src.recommend.recommendation_engine import recommend


df = pd.read_csv(PROJECT_DIR / "datasets" / "processed" / "processed_data.csv")

if df.empty:
    raise Exception("processed_data.csv is empty")

if "last_temp" in df.columns:
    row = df.iloc[0].drop(labels=["last_temp"])
else:
    row = df.iloc[0]

features = row[EXPECTED_COLUMNS].to_dict()

model = load_model()

pred = simulate(model, features, EXPECTED_COLUMNS)
print("Predicted:", pred)

target = pred + 5
result = recommend(model, features, target, EXPECTED_COLUMNS)
print("Recommendation:", result)

assert isinstance(pred, float)
assert "status" in result
assert result["status"] in ["optimal", "suboptimal"]
