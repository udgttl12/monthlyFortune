from dataclasses import dataclass
from typing import Final

from app.schemas.chart import NatalChartResponse

THEME_KEYS: Final = ("career", "money", "love", "risk")

THEME_LABELS: Final[dict[str, str]] = {
    "career": "커리어",
    "money": "재정",
    "love": "관계",
    "risk": "컨디션 관리",
}

ELEMENT_BY_SIGN: Final[dict[str, str]] = {
    "Aries": "fire",
    "Leo": "fire",
    "Sagittarius": "fire",
    "Taurus": "earth",
    "Virgo": "earth",
    "Capricorn": "earth",
    "Gemini": "air",
    "Libra": "air",
    "Aquarius": "air",
    "Cancer": "water",
    "Scorpio": "water",
    "Pisces": "water",
}

ELEMENT_LABELS: Final[dict[str, str]] = {
    "fire": "불",
    "earth": "흙",
    "air": "바람",
    "water": "물",
}

POINT_THEME_WEIGHTS: Final[dict[str, dict[str, float]]] = {
    "Sun": {"career": 1.1, "love": 0.2},
    "Moon": {"love": 0.9, "risk": 0.3},
    "Mercury": {"career": 0.7, "money": 0.5},
    "Venus": {"love": 1.0, "money": 0.6},
    "Mars": {"career": 0.8, "risk": 0.8},
    "Jupiter": {"career": 0.7, "money": 1.0},
    "Saturn": {"career": 0.8, "risk": 0.9},
}

HOUSE_THEME_WEIGHTS: Final[dict[int, dict[str, float]]] = {
    2: {"money": 1.5},
    5: {"love": 1.1},
    6: {"career": 0.6, "risk": 0.5},
    7: {"love": 1.4},
    8: {"money": 0.7, "risk": 1.0},
    10: {"career": 1.5},
    11: {"money": 0.8, "career": 0.5},
    12: {"risk": 1.0},
}


@dataclass(frozen=True)
class NatalProfile:
    sun_sign: str
    moon_sign: str
    rising_sign: str
    dominant_element: str
    dominant_element_label: str
    focus_areas: tuple[str, ...]
    base_scores: dict[str, float]


class ChartEngine:
    def build_natal_profile(self, natal_chart: NatalChartResponse) -> NatalProfile:
        element_counts = {element: 0 for element in ELEMENT_LABELS}
        base_scores = {theme: 0.0 for theme in THEME_KEYS}

        for point in natal_chart.points:
            element = ELEMENT_BY_SIGN.get(point.sign)
            if element is not None:
                element_counts[element] += 1

            point_weights = POINT_THEME_WEIGHTS.get(point.name, {})
            for theme, weight in point_weights.items():
                base_scores[theme] += weight

            if point.house is not None:
                for theme, weight in HOUSE_THEME_WEIGHTS.get(point.house, {}).items():
                    base_scores[theme] += weight

        focus_areas = tuple(
            THEME_LABELS[theme]
            for theme in sorted(
                THEME_KEYS,
                key=lambda theme: (base_scores[theme], THEME_LABELS[theme]),
                reverse=True,
            )[:2]
        )
        dominant_element = max(
            element_counts,
            key=lambda element: (element_counts[element], ELEMENT_LABELS[element]),
        )

        point_map = {point.name: point for point in natal_chart.points}
        return NatalProfile(
            sun_sign=point_map["Sun"].sign,
            moon_sign=point_map["Moon"].sign,
            rising_sign=natal_chart.angles.asc.sign,
            dominant_element=dominant_element,
            dominant_element_label=ELEMENT_LABELS[dominant_element],
            focus_areas=focus_areas,
            base_scores=base_scores,
        )
