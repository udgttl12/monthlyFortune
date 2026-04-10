from app.services.chart_engine import NatalChart
from app.services.transit_engine import MonthlyTransit


class InterpretationEngine:
    def interpret(self, chart: NatalChart, transit: MonthlyTransit) -> dict[str, str]:
        return {
            "career": self._career_message(chart, transit),
            "money": self._money_message(chart, transit),
            "love": self._love_message(chart, transit),
            "risk": self._risk_message(chart, transit),
        }

    def _career_message(self, chart: NatalChart, transit: MonthlyTransit) -> str:
        if transit.intensity >= 7:
            return (
                f"{chart.dominant_element.title()} momentum pushes bold career moves; "
                "prioritize one high-impact objective and protect your focus."
            )
        return (
            f"A {chart.moon_phase_bias} lunar rhythm favors steady progress; "
            "improve systems and document wins for future leverage."
        )

    def _money_message(self, chart: NatalChart, transit: MonthlyTransit) -> str:
        if chart.dominant_element in {"earth", "water"}:
            return (
                "Conservative decisions work best this month; strengthen savings and "
                "review recurring costs before new commitments."
            )
        return (
            "Cash flow is dynamic; channel extra income into debt reduction or "
            "skills that can raise your earning power."
        )

    def _love_message(self, chart: NatalChart, transit: MonthlyTransit) -> str:
        if transit.focus_axis == "self_vs_others":
            return (
                "Relationship harmony depends on clear boundaries; ask directly for "
                "what you need and listen without interrupting."
            )
        return (
            "Shared routines bring closeness; plan one meaningful check-in each week "
            "to keep emotional alignment strong."
        )

    def _risk_message(self, chart: NatalChart, transit: MonthlyTransit) -> str:
        if transit.intensity >= 8:
            return (
                "High planetary tension may trigger overcommitment; avoid rushed "
                "decisions and pause before signing major agreements."
            )
        return (
            "Main risk is distraction by minor urgencies; protect sleep and time-block "
            "priority tasks to prevent burnout."
        )
