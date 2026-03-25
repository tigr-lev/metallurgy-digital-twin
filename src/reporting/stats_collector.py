class StatsCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.total = 0
        
        # Считаем только технические состояния
        self.status_counts = {
            "optimal": 0,
            "stable": 0,
            "unreachable": 0
        }

        # Считаем только корректирующие действия (без "ok")
        self.decision_counts = {
            "overheat": 0,
            "underheat": 0,
            "inefficient": 0
        }

        # Считаем уровни тревоги (без "normal")
        self.severity_counts = {
            "warning": 0,
            "critical": 0
        }

        self.energy_saved = 0.0  # Потенциальная экономия
        self.energy_added = 0.0  # Необходимый догрев

    def update(self, result: dict):
        if not result:
            return

        self.total += 1

        # 1. Технический статус
        s = result.get("status")
        if s in self.status_counts:
            self.status_counts[s] += 1

        # 2. Бизнес-решение
        d = result.get("decision")
        if d in self.decision_counts:
            self.decision_counts[d] += 1

        # 3. Уровень критичности
        sev = result.get("severity")
        if sev in self.severity_counts:
            self.severity_counts[sev] += 1

        # 4. Энергия (защита от None и расчет ROI)
        delta = result.get("delta_energy") or 0.0
        if delta < 0:
            self.energy_saved += abs(delta)
        else:
            self.energy_added += delta

    def to_dict(self):
        """Возвращает плоский словарь для отправки в MQTT"""
        return {
            "stat_total": self.total,
            # Статусы
            "stat_optimal": self.status_counts["optimal"],
            "stat_stable": self.status_counts["stable"],
            "stat_unreachable": self.status_counts["unreachable"],
            # Решения
            "stat_inefficient": self.decision_counts["inefficient"],
            "stat_overheat": self.decision_counts["overheat"],
            "stat_underheat": self.decision_counts["underheat"],
            # Критичность
            "stat_critical": self.severity_counts["critical"],
            "stat_warning": self.severity_counts["warning"],
            # Эффективность (округляем для UI)
            "stat_energy_saved": round(self.energy_saved, 1),
            "stat_energy_added": round(self.energy_added, 1),
        }

# Глобальный объект коллектора
stats_collector = StatsCollector()