from datetime import datetime
from math import fmod

try:
    import swisseph as swe
except ImportError:  # pragma: no cover - runtime fallback
    swe = None


PLANETS = [
    ("Sun", 0),
    ("Moon", 1),
    ("Mercury", 2),
    ("Venus", 3),
    ("Mars", 4),
    ("Jupiter", 5),
    ("Saturn", 6),
]

ASPECT_ANGLES = {
    "Conjunction": 0,
    "Sextile": 60,
    "Square": 90,
    "Trine": 120,
    "Opposition": 180,
}


class ChartEngine:
    def calculate_chart(self, birth_dt: datetime, latitude: float, longitude: float) -> dict:
        planets = self._calculate_planets(birth_dt)
        houses = self._calculate_houses(latitude, longitude)
        aspects = self._calculate_aspects(planets)
        return {"planets": planets, "houses": houses, "aspects": aspects}

    def _calculate_planets(self, birth_dt: datetime) -> list[dict]:
        if swe:
            jd = swe.julday(
                birth_dt.year,
                birth_dt.month,
                birth_dt.day,
                birth_dt.hour + birth_dt.minute / 60.0,
            )
            output = []
            for planet_name, planet_id in PLANETS:
                lon, *_ = swe.calc_ut(jd, planet_id)[0]
                output.append({"name": planet_name, "longitude": round(lon, 2)})
            return output

        seed = birth_dt.toordinal() + birth_dt.hour * 13 + birth_dt.minute
        return [
            {"name": planet_name, "longitude": round(fmod(seed * (idx + 1) * 17.77, 360), 2)}
            for idx, (planet_name, _) in enumerate(PLANETS)
        ]

    def _calculate_houses(self, latitude: float, longitude: float) -> list[dict]:
        base = (latitude + longitude) % 360
        return [
            {"house": house, "cusp": round((base + (house - 1) * 30) % 360, 2)}
            for house in range(1, 13)
        ]

    def _calculate_aspects(self, planets: list[dict]) -> list[dict]:
        aspects = []
        for i, p1 in enumerate(planets):
            for p2 in planets[i + 1 :]:
                diff = abs(p1["longitude"] - p2["longitude"])
                diff = min(diff, 360 - diff)
                for aspect_name, aspect_angle in ASPECT_ANGLES.items():
                    if abs(diff - aspect_angle) <= 6:
                        aspects.append(
                            {
                                "between": f"{p1['name']} - {p2['name']}",
                                "aspect": aspect_name,
                                "orb": round(abs(diff - aspect_angle), 2),
                            }
                        )
                        break
        return aspects
