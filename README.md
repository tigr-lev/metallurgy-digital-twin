AI-Driven Decision Support System for Ladle Furnace

## Environment Configuration
Before running the project, create a `.env` file in the root directory.
A template file `.env.example` is already included in the repository - simply copy it, rename it to `.env`, and provide your actual ThingsBoard device token:
DEVICE_TOKEN=your_thingsboard_device_token_here

Execution Modes
The system can operate in two modes:
1. Standalone Mode
Used for quick validation of the ML model and API without external systems.
What happens:
API (FastAPI) is launched
the model performs predictions
data_streamer simulates a data flow
results are printed in the console
Run:
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run API
uvicorn api.main:app --reload
In a separate terminal:
python scripts/data_streamer.py
(No IoT platform setup required)

2. Extended Mode (IoT + Digital Twin)
Used for system visualization via ThingsBoard.
What happens:
data passes through the API
results are sent via MQTT
displayed on the dashboard
ThingsBoard setup:
Preconfigured files are available in the repository:
thingsboard/device.json
thingsboard/dashboard.json
Steps:
Deploy ThingsBoard (e.g., via Docker)
Import device.json and dashboard.json
Obtain a device's Access Token
Specify the token in the `.env` file
Run the Standalone mode
(IoT mode is optional)

Project Description
Metallurgical production requires precise control of melt temperature, as it directly affects steel quality and energy consumption.
In a ladle furnace (~100 tons), steel is heated using graphite electrodes. The process includes:
arc heating
alloying (bulk and wire additions)
inert gas purging
mixing and repeated temperature measurements
Each batch undergoes several processing iterations until the target temperature is reached.
Task
The goal is to predict the final temperature of the melt based on process parameters.
The problem is formulated as a regression task:
input: process parameters (energy, time, additives, gas, etc.)
output: final temperature
Solution
The project implements a decision support system that:
predicts final temperature (CatBoost)
simulates process behavior
calculates energy adjustment (ΔE)
accounts for physical constraints
The model is used to simulate the process and generate recommendations for the operator.

Exploratory Analysis & ML Modeling
The backend of the digital twin is based on a detailed analysis of historical metallurgical process data
(full pipeline available in notebooks/metallurgy.ipynb).
Instead of feeding raw data directly into the model, a physics-informed feature engineering approach was applied.
Data Cleaning (Physical Validation)
Removed physically impossible states (temperature < 1400°C)
Filtered sensor anomalies (negative reactive power, invalid readings)
Enforced strict temporal ordering to prevent data leakage
all features are computed strictly before the final temperature measurement
Feature Engineering
Energy-related features:
total_arc_energy — total energy input
active/reactive power
energy_rate — heating rate (energy per second)
Material impact:
grouped materials by thermodynamic effect
created aggregated features:
bulk_heat_markers
agg_coolants
Heat losses proxy:
process_duration used as an approximation of natural cooling
Model Selection & Validation
Model: CatBoost Regressor
robust to outliers
effective for tabular industrial data
Performance
MAE (Cross-validation): ~5.95°C
MAE (Test): ~6.03°C
Target requirement (MAE ≤ 6.8°C) — achieved
Baseline Comparison
DummyRegressor: ~8.2°C
Improvement: ~26%
The model demonstrates stable performance with minimal gap between CV and test results.






Process Transformation (As-Is vs To-Be)
As-Is (Traditional Approach)
Temperature is controlled post factum
Decisions are based on operator experience
Underheating leads to additional heating cycles
Overheating → energy overconsumption
Deviations are analyzed after the process is completed
To-Be (ML + Decision Support System)
The model predicts final temperature in advance
The system calculates required energy adjustment (ΔE)
Physical constraints are considered (furnace power limits)
Process simulation becomes possible
Results are available in real time (API / IoT)
Key Change
From reactive control
→ to predictive and controlled operation






Demo
Main Dashboard (Digital Twin View)
![dashboard](demo/screenshots/dashboard.png)










Recommendation Example
![recommendation](demo/screenshots/recommendation.png)










Review.
![review](demo/screenshots/review.png)













API Interaction
![api](demo/screenshots/api.png)








Live Data Simulation
![streamer](demo/screenshots/streamer.png)










Example Scenario

Initial:
Temperature = 1580°C (underheat)

System:
Recommend +3 MJ

Result:
Predicted = 1591°C (within target range)

Data & Feature Engineering (Industrial Logic)

The dataset represents real metallurgical process steps:
- arc heating cycles
- alloy additions (bulk, wire)
- gas injection
- sequential temperature measurements

Key engineering steps:

Data cleaning (physical validation):
- removal of temperatures < 1400°C
- removal of negative reactive power
- correction of invalid timestamps

Causality control:
- all features are computed strictly before final temperature
- verified absence of data leakage

Feature engineering (physics-based):
- total_arc_energy — total energy input
- heating_rate — energy per second
- process_duration — proxy for heat losses
- bulk_heat_markers / agg_coolants — grouped material effects

The model approximates the thermal balance of the process, not just statistical correlations.
Recommendation Engine (Prescriptive Logic)

Unlike standard ML models, this system includes a recommendation layer.

Goal:
Find heating parameters (energy, duration) that achieve target temperature.

Optimization approach:

Grid search over:
- Energy (E): 20–80 MJ
- Duration (t): 1000–4000 sec

Physical constraint:
Power = E / t
5 MW ≤ P ≤ 25 MW

Only feasible solutions are considered.

Objective:
Hard constraint:
- temperature must be within ±2°C

If satisfied:
- minimize energy and time

If not:
- fallback to closest possible temperature

Output:

{
  "status": "optimal | suboptimal",
  "recommended_energy": E,
  "recommended_duration": t,
  "predicted_temp": value
}

Architecture
Data → Feature Engineering → ML Model → Recommendation Engine → API → MQTT → Dashboard

Key Features

- ML-based temperature prediction
- Recommendation engine with constraints
- Physics-informed feature engineering
- Leakage-safe pipeline
- IoT integration
Example Request
{
  "target_temp": 1590,
  "features": {
    "first_temp": 1520,
    "total_arc_energy": 30,
    "total_heating_duration": 2000,
    "Wire 1": 10,
    "gas_volume": 5,
    "process_duration": 3000,
    "energy_rate": 1.2,
    "bulk_heat_markers": 2,
    "agg_coolants": 400,
    "mean_apparent_power": 15,
    "mean_power_factor": 0.85
  }
}

MQTT Integration
The system publishes results via MQTT:
topic: metallurgy/prediction

Message includes:
- predicted temperature
- target
- delta_energy
- status

Optional: ThingsBoard
You can import pre-configured dashboards:
thingsboard/dashboard.json

Limitations
- no real feedback loop
- simplified physical constraints
- offline model
- based on historical data

Notes
This project demonstrates:
- end-to-end ML system
- industrial data preprocessing
- decision support logic
- integration with IoT

Acknowledgments
The initial dataset and the baseline exploratory data analysis (EDA) were developed as part of the Data Science graduation project at Yandex Practicum. This repository expands upon that foundational research, transforming the offline ML model into a full-stack Industrial IoT prototype with real-time streaming, constraints optimization, and digital twin visualization.
