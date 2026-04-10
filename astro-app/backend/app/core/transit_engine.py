from calendar import monthrange
from datetime import date


class TransitEngine:
    def calculate_monthly_transits(self, year: int, month: int, natal_planets: list[dict]) -> list[dict]:
        days = monthrange(year, month)[1]
        events = []
        tracked = natal_planets[:4]
        for day in (1, max(2, days // 3), max(3, (2 * days) // 3), days):
            transit_date = date(year, month, day)
            for idx, planet in enumerate(tracked):
                intensity = ((planet["longitude"] + day * (idx + 2)) % 10) / 10
                if intensity > 0.55:
                    events.append(
                        {
                            "date": transit_date.isoformat(),
                            "title": f"{planet['name']} activation",
                            "impact": "high" if intensity > 0.8 else "medium",
                        }
                    )
        return events
