from pathlib import Path

import joblib


def load_model():
    model_path = Path(__file__).resolve().parents[2] / "artifacts" / "model.joblib"

    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    return joblib.load(model_path)
