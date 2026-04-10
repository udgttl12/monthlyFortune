from dataclasses import dataclass

from app.services.chart_engine import NatalChart


@dataclass(frozen=True)
class MonthlyTransit:
    intensity: int
    focus_axis: str


class TransitEngine:
    AXES = (
        "self_vs_others",
        "security_vs_growth",
        "career_vs_home",
        "logic_vs_emotion",
    )

    def calculate_monthly_transit(self, chart: NatalChart) -> MonthlyTransit:
        intensity = ((chart.year + chart.month) % 9) + 1
        axis_index = (chart.year * chart.month) % len(self.AXES)

        return MonthlyTransit(intensity=intensity, focus_axis=self.AXES[axis_index])
