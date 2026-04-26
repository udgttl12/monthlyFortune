from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import fmean
from typing import Final
from zoneinfo import ZoneInfo

from app.schemas.chart import NatalChartResponse
from app.services.astrology_service import BirthChartContext
from app.services.chart_engine import THEME_KEYS, THEME_LABELS, NatalProfile
from app.services.natal_chart_engine import ASPECT_POLICY, NatalChartEngine

TRANSIT_POINTS: Final = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
NATAL_TARGETS: Final = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC")

POINT_LABELS: Final[dict[str, str]] = {
    "Sun": "태양",
    "Moon": "달",
    "Mercury": "수성",
    "Venus": "금성",
    "Mars": "화성",
    "Jupiter": "목성",
    "Saturn": "토성",
    "ASC": "상승점",
    "MC": "천정점",
}

ASPECT_LABELS: Final[dict[str, str]] = {
    "Conjunction": "합",
    "Sextile": "섹스타일",
    "Square": "스퀘어",
    "Trine": "트라인",
    "Opposition": "충",
}

ASPECT_ORBS: Final[dict[str, float]] = {
    "Conjunction": 3.5,
    "Sextile": 3.0,
    "Square": 3.0,
    "Trine": 3.0,
    "Opposition": 3.5,
}

ASPECT_STRENGTH: Final[dict[str, float]] = {
    "Conjunction": 1.35,
    "Sextile": 1.0,
    "Square": 1.15,
    "Trine": 1.2,
    "Opposition": 1.25,
}

POSITIVE_ASPECTS: Final = {"Sextile", "Trine"}
NEGATIVE_ASPECTS: Final = {"Square", "Opposition"}
SUPPORTIVE_TRANSIT_POINTS: Final = {"Sun", "Venus", "Jupiter"}
CHALLENGING_TRANSIT_POINTS: Final = {"Mars", "Saturn"}

TRANSIT_THEME_WEIGHTS: Final[dict[str, dict[str, float]]] = {
    "Sun": {"career": 0.9, "love": 0.3},
    "Moon": {"love": 0.7, "risk": 0.2},
    "Mercury": {"career": 0.6, "money": 0.5},
    "Venus": {"love": 1.1, "money": 0.7},
    "Mars": {"career": 0.6, "risk": 1.1},
    "Jupiter": {"career": 0.8, "money": 0.9, "love": 0.4},
    "Saturn": {"career": 0.8, "money": 0.4, "risk": 1.0},
}

NATAL_THEME_WEIGHTS: Final[dict[str, dict[str, float]]] = {
    "Sun": {"career": 0.8},
    "Moon": {"love": 0.9, "risk": 0.3},
    "Mercury": {"career": 0.5, "money": 0.4},
    "Venus": {"love": 0.9, "money": 0.7},
    "Mars": {"career": 0.6, "risk": 0.7},
    "Jupiter": {"money": 0.7, "career": 0.5},
    "Saturn": {"career": 0.7, "risk": 0.8},
    "ASC": {"love": 0.3, "risk": 0.4},
    "MC": {"career": 1.1, "money": 0.3},
}


@dataclass(frozen=True)
class TransitEvent:
    date: date
    theme: str
    tone: str
    score: float
    headline: str
    detail: str


@dataclass(frozen=True)
class DailyTransitScore:
    date: date
    total_score: float
    category_scores: dict[str, float]
    positive_events: list[TransitEvent]
    negative_events: list[TransitEvent]


@dataclass(frozen=True)
class TransitWindow:
    start_date: date
    end_date: date
    label: str


@dataclass(frozen=True)
class MonthlyTransitAnalysis:
    year: int
    month: int
    title: str
    focus_area_keys: tuple[str, ...]
    focus_area_labels: tuple[str, ...]
    top_theme_key: str
    top_theme_label: str
    intensity_score: int
    total_score: float
    category_totals: dict[str, float]
    daily_scores: list[DailyTransitScore]
    lucky_days: list[DailyTransitScore]
    caution_days: list[DailyTransitScore]
    evidence: list[TransitEvent]
    lucky_window: TransitWindow
    caution_window: TransitWindow


class TransitEngine:
    def __init__(self, natal_chart_engine: NatalChartEngine) -> None:
        self.natal_chart_engine = natal_chart_engine

    def calculate_monthly_transit(
        self,
        context: BirthChartContext,
        profile: NatalProfile,
        year: int,
        month: int,
    ) -> MonthlyTransitAnalysis:
        daily_scores = [
            self._score_day(
                context=context,
                profile=profile,
                target_date=date(year, month, day),
            )
            for day in range(1, self._days_in_month(year, month) + 1)
        ]

        category_totals = {theme: 0.0 for theme in THEME_KEYS}
        all_events: list[TransitEvent] = []
        for daily_score in daily_scores:
            for theme, value in daily_score.category_scores.items():
                category_totals[theme] += value
            all_events.extend(daily_score.positive_events)
            all_events.extend(daily_score.negative_events)

        lucky_days = sorted(daily_scores, key=lambda day: (day.total_score, day.date.toordinal()), reverse=True)[:3]
        caution_days = sorted(daily_scores, key=lambda day: (day.total_score, day.date.toordinal()))[:3]
        evidence = sorted(all_events, key=lambda event: (abs(event.score), event.date.toordinal()), reverse=True)[:4]

        focus_area_keys = tuple(
            sorted(
                THEME_KEYS,
                key=lambda theme: (abs(category_totals[theme]), THEME_LABELS[theme]),
                reverse=True,
            )[:2]
        )
        focus_area_labels = tuple(THEME_LABELS[theme] for theme in focus_area_keys)
        top_theme_key = focus_area_keys[0]
        intensity_score = self._calculate_intensity_score(daily_scores)
        total_score = round(sum(day.total_score for day in daily_scores), 2)

        return MonthlyTransitAnalysis(
            year=year,
            month=month,
            title=self._build_title(top_theme_key, total_score, intensity_score),
            focus_area_keys=focus_area_keys,
            focus_area_labels=focus_area_labels,
            top_theme_key=top_theme_key,
            top_theme_label=THEME_LABELS[top_theme_key],
            intensity_score=intensity_score,
            total_score=total_score,
            category_totals={theme: round(score, 2) for theme, score in category_totals.items()},
            daily_scores=daily_scores,
            lucky_days=lucky_days,
            caution_days=caution_days,
            evidence=evidence,
            lucky_window=self._select_window(daily_scores, top_theme_key, reverse=True),
            caution_window=self._select_window(daily_scores, top_theme_key, reverse=False),
        )

    def _score_day(
        self,
        context: BirthChartContext,
        profile: NatalProfile,
        target_date: date,
    ) -> DailyTransitScore:
        transit_dt_local = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            12,
            0,
            tzinfo=ZoneInfo(context.location.timezone),
        )
        transit_chart = self.natal_chart_engine.calculate_chart(
            birth_dt_local=transit_dt_local,
            latitude=context.location.latitude,
            longitude=context.location.longitude,
        )
        natal_targets = self._build_natal_target_map(context.natal_chart)
        transit_points = {point["name"]: point for point in transit_chart["points"]}

        category_scores = {theme: 0.0 for theme in THEME_KEYS}
        events: list[TransitEvent] = []

        for transit_name in TRANSIT_POINTS:
            transit_point = transit_points[transit_name]
            for natal_name in NATAL_TARGETS:
                natal_longitude = natal_targets[natal_name]
                aspect_name, orb = self._find_aspect(transit_point["longitude"], natal_longitude)
                if aspect_name is None:
                    continue

                contributions = self._build_category_contributions(
                    transit_name=transit_name,
                    natal_name=natal_name,
                    aspect_name=aspect_name,
                    orb=orb,
                    profile=profile,
                )
                if not contributions:
                    continue

                dominant_theme = max(
                    contributions,
                    key=lambda theme: (abs(contributions[theme]), THEME_LABELS[theme]),
                )
                dominant_score = contributions[dominant_theme]
                tone = "supportive" if dominant_score >= 0 else "challenging"
                event = TransitEvent(
                    date=target_date,
                    theme=dominant_theme,
                    tone=tone,
                    score=round(dominant_score, 2),
                    headline=f"{POINT_LABELS[transit_name]} {ASPECT_LABELS[aspect_name]} {POINT_LABELS[natal_name]}",
                    detail=self._build_event_detail(
                        transit_name=transit_name,
                        natal_name=natal_name,
                        aspect_name=aspect_name,
                        dominant_theme=dominant_theme,
                        tone=tone,
                    ),
                )
                events.append(event)
                for theme, value in contributions.items():
                    category_scores[theme] += value

        positive_events = sorted(
            [event for event in events if event.score >= 0],
            key=lambda event: (event.score, event.date.toordinal()),
            reverse=True,
        )[:3]
        negative_events = sorted(
            [event for event in events if event.score < 0],
            key=lambda event: (event.score, event.date.toordinal()),
        )[:3]
        total_score = round(sum(category_scores.values()), 2)

        return DailyTransitScore(
            date=target_date,
            total_score=total_score,
            category_scores={theme: round(score, 2) for theme, score in category_scores.items()},
            positive_events=positive_events,
            negative_events=negative_events,
        )

    def _build_category_contributions(
        self,
        transit_name: str,
        natal_name: str,
        aspect_name: str,
        orb: float,
        profile: NatalProfile,
    ) -> dict[str, float]:
        polarity = self._get_polarity(transit_name=transit_name, natal_name=natal_name, aspect_name=aspect_name)
        if polarity == 0:
            return {}

        orb_ratio = max(0.45, 1 - (orb / ASPECT_ORBS[aspect_name]))
        aspect_strength = ASPECT_STRENGTH[aspect_name] * orb_ratio
        contributions: dict[str, float] = {}

        for theme in THEME_KEYS:
            transit_weight = TRANSIT_THEME_WEIGHTS.get(transit_name, {}).get(theme, 0.0)
            natal_weight = NATAL_THEME_WEIGHTS.get(natal_name, {}).get(theme, 0.0)
            if transit_weight == 0 and natal_weight == 0:
                continue

            importance = max(transit_weight, natal_weight) + (min(transit_weight, natal_weight) * 0.5)
            profile_bias = 1.0 + (profile.base_scores.get(theme, 0.0) / 18.0)
            contributions[theme] = round(polarity * aspect_strength * importance * profile_bias, 2)

        return contributions

    def _build_event_detail(
        self,
        transit_name: str,
        natal_name: str,
        aspect_name: str,
        dominant_theme: str,
        tone: str,
    ) -> str:
        if tone == "supportive":
            motion = "부드럽게 밀어주는"
        else:
            motion = "긴장을 만들며 조율을 요구하는"

        return (
            f"{POINT_LABELS[transit_name]}이 {POINT_LABELS[natal_name]}과 {ASPECT_LABELS[aspect_name]}을 이루며 "
            f"{THEME_LABELS[dominant_theme]} 흐름에 {motion} 신호를 만듭니다."
        )

    def _build_natal_target_map(self, natal_chart: NatalChartResponse) -> dict[str, float]:
        target_map = {point.name: point.longitude for point in natal_chart.points}
        target_map["ASC"] = natal_chart.angles.asc.longitude
        target_map["MC"] = natal_chart.angles.mc.longitude
        return target_map

    def _find_aspect(self, transit_longitude: float, natal_longitude: float) -> tuple[str | None, float]:
        diff = self._normalize(transit_longitude - natal_longitude)
        for aspect_name, aspect_angle, _ in ASPECT_POLICY:
            max_orb = ASPECT_ORBS[aspect_name]
            delta = self._aspect_delta(diff, aspect_angle)
            orb = abs(delta)
            if orb <= max_orb:
                return aspect_name, round(orb, 2)
        return None, 0.0

    def _get_polarity(self, transit_name: str, natal_name: str, aspect_name: str) -> float:
        if aspect_name in POSITIVE_ASPECTS:
            return 1.0
        if aspect_name in NEGATIVE_ASPECTS:
            return -1.0

        if transit_name in SUPPORTIVE_TRANSIT_POINTS:
            return 0.9
        if transit_name in CHALLENGING_TRANSIT_POINTS:
            if natal_name in {"MC", "Sun"}:
                return 0.2
            return -0.85
        if transit_name == "Moon":
            return 0.35
        return 0.5

    def _calculate_intensity_score(self, daily_scores: list[DailyTransitScore]) -> int:
        average_abs = fmean(abs(day.total_score) for day in daily_scores)
        peak_abs = max(abs(day.total_score) for day in daily_scores)
        raw_score = 1.5 + (average_abs * 1.2) + (peak_abs * 0.45)
        return max(1, min(10, round(raw_score)))

    def _build_title(self, top_theme_key: str, total_score: float, intensity_score: int) -> str:
        if total_score >= 6:
            mood = "확장이 두드러지는"
        elif total_score >= 0:
            mood = "정비가 잘 먹히는"
        elif intensity_score >= 8:
            mood = "집중 조율이 필요한"
        else:
            mood = "균형을 다시 잡는"

        return f"{THEME_LABELS[top_theme_key]} {mood} 달"

    def _select_window(
        self,
        daily_scores: list[DailyTransitScore],
        theme_key: str,
        reverse: bool,
    ) -> TransitWindow:
        best_start_index = 0
        best_score: float | None = None
        window_size = min(3, len(daily_scores))

        for start_index in range(0, len(daily_scores) - window_size + 1):
            chunk = daily_scores[start_index : start_index + window_size]
            chunk_score = sum(day.category_scores[theme_key] for day in chunk)
            if best_score is None:
                best_score = chunk_score
                best_start_index = start_index
                continue

            should_replace = chunk_score > best_score if reverse else chunk_score < best_score
            if should_replace:
                best_score = chunk_score
                best_start_index = start_index

        selected = daily_scores[best_start_index : best_start_index + window_size]
        start_date = selected[0].date
        end_date = selected[-1].date
        theme_label = THEME_LABELS[theme_key]
        mood = "흐름이 열리는" if reverse else "속도 조절이 필요한"

        return TransitWindow(
            start_date=start_date,
            end_date=end_date,
            label=f"{start_date.month}/{start_date.day}-{end_date.month}/{end_date.day} {theme_label} {mood} 구간",
        )

    def _days_in_month(self, year: int, month: int) -> int:
        if month == 12:
            return 31
        next_month = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
        current_month = date(year, month, 1)
        return (next_month - current_month).days

    def _normalize(self, angle: float) -> float:
        return angle % 360

    def _shortest_signed_angle(self, angle: float) -> float:
        normalized = (angle + 180) % 360 - 180
        if normalized == -180:
            return 180.0
        return normalized

    def _aspect_delta(self, diff: float, aspect_angle: float) -> float:
        deltas = [self._shortest_signed_angle(diff - aspect_angle)]
        if aspect_angle not in {0.0, 180.0}:
            deltas.append(self._shortest_signed_angle(diff - (360.0 - aspect_angle)))

        return min(deltas, key=lambda value: abs(value))
