from src.inference.simulate import simulate

TEMP_TOLERANCE = 3.0
CRITICAL_TOLERANCE = 10.0


def objective(pred, target, E, t):
    temp_error = abs(pred - target)
    return (temp_error * 1000) + (E * 1.5) + (t * 0.5)


def _get_business_layer(pred, target, delta_energy, base_E, tol):
    """Транслирует математику в бизнес-статусы (с учетом % экономии)"""
    delta_temp = pred - target

    # 1. Температура в норме
    if abs(delta_temp) <= tol:
        # Экономия больше 5% от базовой энергии
        if base_E > 0 and delta_energy <= -0.05 * base_E:
            return "inefficient", "reduce_energy", "warning", "Температура в норме, но возможна экономия энергии."
        return "ok", "no_action", "normal", "Режим оптимален."

    # 2. Перегрев
    if delta_temp > tol:
        severity = "critical" if delta_temp > CRITICAL_TOLERANCE else "warning"
        return "overheat", "reduce_energy", severity, f"Перегрев на {delta_temp:.1f}°C. Снизить энергию."

    # 3. Недогрев
    severity = "critical" if delta_temp < -CRITICAL_TOLERANCE else "warning"
    return "underheat", "increase_energy", severity, f"Недогрев на {abs(delta_temp):.1f}°C. Добавить энергию."


def recommend(model, base_features, target, expected_columns):
    if base_features is None or expected_columns is None:
        raise Exception("base_features and expected_columns are required")

    if "total_arc_energy" not in base_features:
        raise Exception("base_features must contain total_arc_energy")

    current_pred = simulate(model, base_features, expected_columns)
    base_E = float(base_features["total_arc_energy"])
    base_t = float(base_features.get("total_heating_duration", 2000))

    # --- 1. ИНИЦИАЛИЗАЦИЯ (Фолбэк-защита от пустых сеток) ---
    min_error = abs(current_pred - target)
    closest = (base_E, base_t, current_pred)
    best_cost = objective(current_pred, target, base_E, base_t)
    best = (base_E, base_t, current_pred)

    # --- 2. ДИНАМИЧЕСКАЯ СЕТКА И АДАПТИВНАЯ МОЩНОСТЬ ---
    base_P = (base_E / base_t) * 1000 if base_t > 0 else 0
    min_P = base_P * 0.5
    max_P = base_P * 1.5

    start_E = int(max(1, base_E * 0.8))
    end_E = int(base_E * 1.5) + 2
    step_E = max(1, (end_E - start_E) // 20)

    start_t = int(max(10, base_t * 0.8))
    end_t = int(base_t * 1.5) + 2
    step_t = max(10, (end_t - start_t) // 20)

    for E in range(start_E, end_E + 1, step_E):
        for t in range(start_t, end_t + 1, step_t):
            if t == 0:
                continue

            P = (E / t) * 1000
            if not (min_P <= P <= max_P):
                continue

            f = base_features.copy()
            f["total_arc_energy"] = float(E)
            f["total_heating_duration"] = float(t)
            
            f["energy_rate"] = E / t
            pf = f.get("mean_power_factor", 1.0)
            if not isinstance(pf, (int, float)) or pf == 0:
                pf = 1.0
            f["mean_apparent_power"] = P / pf
            f.pop("total_arc_duration", None)

            pred = simulate(model, f, expected_columns)
            error = abs(pred - target)

            if error < min_error:
                min_error = error
                closest = (E, t, pred)

            cost = objective(pred, target, E, t)
            if cost < best_cost:
                best_cost = cost
                best = (E, t, pred)

    # --- 3. ВОЗВРАТ РЕЗУЛЬТАТОВ ---
    if min_error > TEMP_TOLERANCE:
        delta = closest[0] - base_E
        dec, act, sev, msg = _get_business_layer(closest[2], target, delta, base_E, TEMP_TOLERANCE)
        return {
            "status": "unreachable",
            "decision": dec,
            "action": act,
            "severity": sev,
            "message": msg,
            "E": float(closest[0]),
            "t": float(closest[1]),
            "pred": float(closest[2]),
            "delta_energy": float(delta)
        }

    delta = best[0] - base_E
    dec, act, sev, msg = _get_business_layer(best[2], target, delta, base_E, TEMP_TOLERANCE)
    
    # Разделяем визуально идеальный заводской режим и найденную оптимизацию
    final_status = "stable" if abs(delta) < 0.1 else "optimal"

    return {
        "status": final_status,
        "decision": dec,
        "action": act,
        "severity": sev,
        "message": msg,
        "E": float(best[0]),
        "t": float(best[1]),
        "pred": float(best[2]),
        "delta_energy": float(delta)
    }