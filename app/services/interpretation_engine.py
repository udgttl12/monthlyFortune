from typing import Optional

from app.schemas.horoscope import (
    HoroscopeDateInsight,
    HoroscopeEvidence,
    HoroscopeSections,
    MonthlyHoroscopeLLMResponse,
    MonthlyHoroscopeResponse,
    YearlyHoroscopeResponse,
    YearlyMonthOverview,
)
from app.services.chart_engine import THEME_LABELS, NatalProfile
from app.services.transit_engine import MonthlyTransitAnalysis


class InterpretationEngine:
    def build_yearly_response(
        self,
        year: int,
        profile: NatalProfile,
        monthly_analyses: list[MonthlyTransitAnalysis],
    ) -> YearlyHoroscopeResponse:
        return YearlyHoroscopeResponse(
            year=year,
            profileSummary=self._build_profile_summary(profile),
            months=[
                YearlyMonthOverview(
                    month=analysis.month,
                    title=analysis.title,
                    focusAreas=list(analysis.focus_area_labels),
                    intensityScore=analysis.intensity_score,
                    topTheme=analysis.top_theme_label,
                    luckyWindow={
                        "startDate": analysis.lucky_window.start_date,
                        "endDate": analysis.lucky_window.end_date,
                        "label": analysis.lucky_window.label,
                    },
                    cautionWindow={
                        "startDate": analysis.caution_window.start_date,
                        "endDate": analysis.caution_window.end_date,
                        "label": analysis.caution_window.label,
                    },
                )
                for analysis in monthly_analyses
            ],
        )

    def build_monthly_response(
        self,
        analysis: MonthlyTransitAnalysis,
        profile: NatalProfile,
    ) -> MonthlyHoroscopeResponse:
        sections = HoroscopeSections(
            career=self._build_section_text("career", analysis, profile),
            money=self._build_section_text("money", analysis, profile),
            love=self._build_section_text("love", analysis, profile),
            risk=self._build_section_text("risk", analysis, profile),
        )
        summary = self._build_summary(analysis, profile)

        return MonthlyHoroscopeResponse(
            year=analysis.year,
            month=analysis.month,
            summary=summary,
            sections=sections,
            luckyDates=[self._build_day_insight(day, positive=True) for day in analysis.lucky_days],
            cautionDates=[self._build_day_insight(day, positive=False) for day in analysis.caution_days],
            evidence=[
                HoroscopeEvidence(
                    date=event.date,
                    headline=event.headline,
                    detail=event.detail,
                    tone=event.tone,
                )
                for event in analysis.evidence
            ],
            llmEnhanced=False,
        )

    def apply_llm_enhancement(
        self,
        fallback: MonthlyHoroscopeResponse,
        enhancement: Optional[MonthlyHoroscopeLLMResponse],
    ) -> MonthlyHoroscopeResponse:
        if enhancement is None:
            return fallback

        lucky_dates = []
        for index, fallback_item in enumerate(fallback.lucky_dates):
            if index < len(enhancement.lucky_dates):
                llm_item = enhancement.lucky_dates[index]
                lucky_dates.append(
                    HoroscopeDateInsight(
                        date=fallback_item.date,
                        label=llm_item.label,
                        reason=llm_item.reason,
                    )
                )
            else:
                lucky_dates.append(fallback_item)

        caution_dates = []
        for index, fallback_item in enumerate(fallback.caution_dates):
            if index < len(enhancement.caution_dates):
                llm_item = enhancement.caution_dates[index]
                caution_dates.append(
                    HoroscopeDateInsight(
                        date=fallback_item.date,
                        label=llm_item.label,
                        reason=llm_item.reason,
                    )
                )
            else:
                caution_dates.append(fallback_item)

        evidence = []
        for index, fallback_item in enumerate(fallback.evidence):
            if index < len(enhancement.evidence):
                llm_item = enhancement.evidence[index]
                evidence.append(
                    HoroscopeEvidence(
                        date=fallback_item.date,
                        headline=llm_item.headline,
                        detail=llm_item.detail,
                        tone=fallback_item.tone,
                    )
                )
            else:
                evidence.append(fallback_item)

        return MonthlyHoroscopeResponse(
            year=fallback.year,
            month=fallback.month,
            summary=enhancement.summary,
            sections=enhancement.sections,
            luckyDates=lucky_dates,
            cautionDates=caution_dates,
            evidence=evidence,
            llmEnhanced=True,
        )

    def _build_profile_summary(self, profile: NatalProfile) -> str:
        return (
            f"태양은 {profile.sun_sign}, 달은 {profile.moon_sign}, 상승궁은 {profile.rising_sign}에 있습니다. "
            f"차트에서 {profile.dominant_element_label} 기질이 두드러지고, 올해는 "
            f"{profile.focus_areas[0]}와 {profile.focus_areas[1]} 흐름을 중심으로 읽는 것이 좋습니다."
        )

    def _build_summary(self, analysis: MonthlyTransitAnalysis, profile: NatalProfile) -> str:
        if analysis.total_score >= 6:
            stance = "새로운 시도와 확장에 힘을 실어도 좋은 흐름"
        elif analysis.total_score >= 0:
            stance = "정리와 실행을 함께 가져가면 성과가 나는 흐름"
        elif analysis.intensity_score >= 8:
            stance = "감정과 일정의 과열을 줄이고 우선순위를 다시 잡아야 하는 흐름"
        else:
            stance = "무리한 확장보다 균형 회복을 먼저 보는 흐름"

        return (
            f"{analysis.month}월은 {analysis.top_theme_label} 이슈가 가장 크게 올라옵니다. "
            f"{profile.focus_areas[0]} 성향을 바탕으로 움직이되, 전체적으로는 {stance}입니다."
        )

    def _build_section_text(
        self,
        theme_key: str,
        analysis: MonthlyTransitAnalysis,
        profile: NatalProfile,
    ) -> str:
        score = analysis.category_totals[theme_key]
        focus = THEME_LABELS[theme_key]
        strongest_evidence = next(
            (event for event in analysis.evidence if event.theme == theme_key),
            analysis.evidence[0] if analysis.evidence else None,
        )
        evidence_text = strongest_evidence.headline if strongest_evidence is not None else "큰 흐름은 비교적 완만합니다"

        if score >= 4:
            tone = "앞으로 밀어붙일 힘이 있습니다"
        elif score >= 0:
            tone = "천천히 정리하면 성과를 만들 수 있습니다"
        elif score <= -4:
            tone = "속도를 줄이고 방어적으로 움직이는 편이 좋습니다"
        else:
            tone = "작은 조율은 필요하지만 충분히 다룰 수 있습니다"

        if theme_key == "career":
            guidance = "해야 할 일을 넓히기보다 가장 중요한 일 하나를 끝까지 밀어보세요."
        elif theme_key == "money":
            guidance = "지출 구조를 먼저 정리하고, 큰 결정은 좋은 날짜 쪽으로 맞추는 편이 안전합니다."
        elif theme_key == "love":
            guidance = "상대의 반응을 추측하기보다 직접적이고 차분한 대화가 도움이 됩니다."
        else:
            guidance = "일정 과밀과 피로 누적을 줄이고 회복 시간을 먼저 확보하세요."

        return f"{focus} 영역은 {tone}. 근거로는 {evidence_text} 흐름이 보이며, {guidance}"

    def _build_day_insight(self, day, positive: bool) -> HoroscopeDateInsight:
        source_event = (
            day.positive_events[0]
            if positive and day.positive_events
            else day.negative_events[0]
            if day.negative_events
            else (day.positive_events[0] if day.positive_events else None)
        )
        theme_key = (
            source_event.theme
            if source_event is not None
            else max(day.category_scores, key=lambda theme: abs(day.category_scores[theme]))
        )
        theme_label = THEME_LABELS[theme_key]

        if positive:
            label = f"{theme_label}에 힘이 실리는 날"
            reason = (
                source_event.detail
                if source_event is not None
                else f"{theme_label} 관련 선택을 진행하기 좋은 흐름입니다."
            )
        else:
            label = f"{theme_label} 속도 조절이 필요한 날"
            reason = (
                source_event.detail
                if source_event is not None
                else f"{theme_label} 관련 판단이 흔들릴 수 있어 확인을 먼저 하는 편이 좋습니다."
            )

        return HoroscopeDateInsight(date=day.date, label=label, reason=reason)
