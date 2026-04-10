from dataclasses import dataclass


@dataclass(frozen=True)
class NatalChart:
    year: int
    month: int
    dominant_element: str
    moon_phase_bias: str


class ChartEngine:
    ELEMENTS = ("fire", "earth", "air", "water")
    PHASES = ("new", "waxing", "full", "waning")

    def build_monthly_chart(self, year: int, month: int) -> NatalChart:
        seed = (year * 37) + (month * 17)
        element = self.ELEMENTS[seed % len(self.ELEMENTS)]
        phase = self.PHASES[(seed // 3) % len(self.PHASES)]

        return NatalChart(
            year=year,
            month=month,
            dominant_element=element,
            moon_phase_bias=phase,
        )
