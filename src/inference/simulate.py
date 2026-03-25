import pandas as pd


def simulate(model, features_dict, expected_columns):
    missing = set(expected_columns) - set(features_dict.keys())
    extra = set(features_dict.keys()) - set(expected_columns)

    if missing:
        raise Exception(f"Missing features: {missing}")

    if extra:
        raise Exception(f"Unexpected features: {extra}")

    for k, v in features_dict.items():
        if not isinstance(v, (int, float)):
            raise Exception(f"{k} must be numeric")

    df = pd.DataFrame([features_dict], columns=expected_columns)
    prediction = model.predict(df)

    return float(prediction[0])
