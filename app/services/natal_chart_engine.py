from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import swisseph as swe

SIGN_NAMES: Final = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)

BODY_IDS: Final = (
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
    ("North Node", swe.MEAN_NODE),
    ("Lilith", swe.MEAN_APOG),
    ("Chiron", swe.CHIRON),
)

ASPECT_POLICY: Final = (
    ("Conjunction", 0.0, 8.0),
    ("Sextile", 60.0, 6.0),
    ("Square", 90.0, 6.0),
    ("Trine", 120.0, 6.0),
    ("Opposition", 180.0, 8.0),
)

POINT_ORDER: Final = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "North Node",
    "Lilith",
    "Chiron",
    "Fortune",
    "Vertex",
]

ANGLE_NAMES: Final = {"ASC", "DSC", "MC", "IC"}


@dataclass(frozen=True)
class CalculatedPoint:
    name: str
    longitude: float
    speed: float
    retrograde: bool
    house: int | None = None


class NatalChartEngine:
    def __init__(self, ephemeris_path: Path | None = None) -> None:
        self.ephemeris_path = ephemeris_path or Path(__file__).resolve().parents[1] / "data" / "ephe"
        self._ensure_ephemeris_path()

    def calculate_chart(self, birth_dt_local: datetime, latitude: float, longitude: float) -> dict:
        self._ensure_ephemeris_path()
        birth_dt_utc = birth_dt_local.astimezone(UTC)
        julian_day = swe.julday(
            birth_dt_utc.year,
            birth_dt_utc.month,
            birth_dt_utc.day,
            birth_dt_utc.hour + (birth_dt_utc.minute / 60.0),
        )

        houses, angles = self._calculate_houses(julian_day, latitude, longitude)
        points = self._calculate_points(julian_day, angles["asc"].longitude)
        special_points = self._calculate_special_points(points, angles["asc"].longitude, angles["mc"].longitude, angles["vertex"].longitude)
        all_points = points + special_points
        sorted_points = sorted(all_points, key=lambda point: POINT_ORDER.index(point.name))
        aspects = self._calculate_aspects(sorted_points, angles)

        return {
            "points": [self._serialize_point(point) for point in sorted_points],
            "angles": {
                "asc": self._serialize_angle(angles["asc"].longitude),
                "mc": self._serialize_angle(angles["mc"].longitude),
            },
            "houses": houses,
            "aspects": aspects,
        }

    def _ensure_ephemeris_path(self) -> None:
        swe.set_ephe_path(str(self.ephemeris_path))

    def _calculate_points(self, julian_day: float, asc_longitude: float) -> list[CalculatedPoint]:
        points: list[CalculatedPoint] = []
        for name, body_id in BODY_IDS:
            values, _, _ = swe.calc_ut(julian_day, body_id, swe.FLG_SPEED)
            longitude = self._normalize(values[0])
            speed = values[3]
            points.append(
                CalculatedPoint(
                    name=name,
                    longitude=longitude,
                    speed=speed,
                    retrograde=speed < 0,
                    house=self._whole_sign_house(longitude, asc_longitude),
                )
            )
        return points

    def _calculate_special_points(
        self,
        points: list[CalculatedPoint],
        asc_longitude: float,
        mc_longitude: float,
        vertex_longitude: float,
    ) -> list[CalculatedPoint]:
        point_map = {point.name: point for point in points}
        sun = point_map["Sun"]
        moon = point_map["Moon"]
        day_chart = (sun.house or 1) >= 7

        if day_chart:
            fortune_longitude = self._normalize(asc_longitude + moon.longitude - sun.longitude)
        else:
            fortune_longitude = self._normalize(asc_longitude + sun.longitude - moon.longitude)

        return [
            CalculatedPoint(
                name="Fortune",
                longitude=fortune_longitude,
                speed=0.0,
                retrograde=False,
                house=self._whole_sign_house(fortune_longitude, asc_longitude),
            ),
            CalculatedPoint(
                name="Vertex",
                longitude=self._normalize(vertex_longitude),
                speed=0.0,
                retrograde=False,
                house=self._whole_sign_house(vertex_longitude, asc_longitude),
            ),
        ]

    def _calculate_houses(self, julian_day: float, latitude: float, longitude: float) -> tuple[list[dict], dict[str, CalculatedPoint]]:
        cusps, ascmc = swe.houses_ex(julian_day, latitude, longitude, b"W")
        asc_longitude = self._normalize(ascmc[0])
        mc_longitude = self._normalize(ascmc[1])
        vertex_longitude = self._normalize(ascmc[3])

        houses = []
        for house_number in range(1, 13):
            cusp_longitude = self._normalize(cusps[house_number])
            houses.append(
                {
                    "houseNumber": house_number,
                    "sign": self._sign_name(cusp_longitude),
                    "cuspLongitude": round(cusp_longitude, 6),
                }
            )

        angles = {
            "asc": CalculatedPoint("ASC", asc_longitude, 0.0, False, 1),
            "mc": CalculatedPoint("MC", mc_longitude, 0.0, False, 10),
            "dsc": CalculatedPoint("DSC", self._normalize(asc_longitude + 180), 0.0, False, 7),
            "ic": CalculatedPoint("IC", self._normalize(mc_longitude + 180), 0.0, False, 4),
            "vertex": CalculatedPoint("Vertex", vertex_longitude, 0.0, False, self._whole_sign_house(vertex_longitude, asc_longitude)),
        }
        return houses, angles

    def _calculate_aspects(self, points: list[CalculatedPoint], angles: dict[str, CalculatedPoint]) -> list[dict]:
        aspect_points = points + [angles["asc"], angles["mc"], angles["dsc"], angles["ic"]]
        aspects: list[dict] = []

        for index, first in enumerate(aspect_points):
            for second in aspect_points[index + 1 :]:
                display_first, display_second = self._ordered_aspect_points(first, second)
                diff = self._normalize(display_second.longitude - display_first.longitude)
                for aspect_name, aspect_angle, max_orb in ASPECT_POLICY:
                    delta = self._aspect_delta(diff, aspect_angle)
                    orb = abs(delta)
                    if orb > max_orb:
                        continue

                    if display_first.name in ANGLE_NAMES or display_second.name in ANGLE_NAMES:
                        applying = delta > 0
                    else:
                        relative_speed = display_second.speed - display_first.speed
                        applying = delta * relative_speed < 0
                    aspects.append(
                        {
                            "pointA": display_first.name,
                            "pointB": display_second.name,
                            "aspect": aspect_name,
                            "orb": round(orb, 2),
                            "applying": applying,
                        }
                    )
                    break

        return sorted(aspects, key=lambda aspect: (aspect["orb"], aspect["pointA"], aspect["pointB"]))

    def _serialize_point(self, point: CalculatedPoint) -> dict:
        angle = self._serialize_angle(point.longitude)
        return {
            "name": point.name,
            "longitude": round(point.longitude, 6),
            "sign": angle["sign"],
            "degree": angle["degree"],
            "minute": angle["minute"],
            "retrograde": point.retrograde,
            "house": point.house,
        }

    def _serialize_angle(self, longitude: float) -> dict:
        normalized = self._normalize(longitude)
        sign_index = int(normalized // 30)
        degree_float = normalized - (sign_index * 30)
        degree = int(degree_float)
        minute = int(round((degree_float - degree) * 60))

        if minute == 60:
            minute = 0
            degree += 1
        if degree == 30:
            degree = 0
            sign_index = (sign_index + 1) % 12

        return {
            "longitude": round(normalized, 6),
            "sign": SIGN_NAMES[sign_index],
            "degree": degree,
            "minute": minute,
        }

    def _whole_sign_house(self, longitude: float, asc_longitude: float) -> int:
        asc_sign_index = int(self._normalize(asc_longitude) // 30)
        point_sign_index = int(self._normalize(longitude) // 30)
        return ((point_sign_index - asc_sign_index) % 12) + 1

    def _sign_name(self, longitude: float) -> str:
        return SIGN_NAMES[int(self._normalize(longitude) // 30)]

    def _normalize(self, angle: float) -> float:
        return angle % 360

    def _shortest_signed_angle(self, angle: float) -> float:
        normalized = (angle + 180) % 360 - 180
        if normalized == -180:
            return 180.0
        return normalized

    def _ordered_aspect_points(
        self,
        first: CalculatedPoint,
        second: CalculatedPoint,
    ) -> tuple[CalculatedPoint, CalculatedPoint]:
        if first.name in ANGLE_NAMES and second.name not in ANGLE_NAMES:
            return first, second
        if second.name in ANGLE_NAMES and first.name not in ANGLE_NAMES:
            return second, first
        return first, second

    def _aspect_delta(self, diff: float, aspect_angle: float) -> float:
        deltas = [self._shortest_signed_angle(diff - aspect_angle)]
        if aspect_angle not in {0.0, 180.0}:
            deltas.append(self._shortest_signed_angle(diff - (360.0 - aspect_angle)))

        return min(deltas, key=lambda value: abs(value))
