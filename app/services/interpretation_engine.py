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
        enhancement: MonthlyHoroscopeLLMResponse | None,
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
            f"{profile.sun_sign} 태양, {profile.moon_sign} 달, {profile.rising_sign} 상승점을 가진 차트입니다. "
            f"기본 기질은 {profile.dominant_element_label} 원소가 강하고, 올해는 "
            f"{profile.focus_areas[0]}와 {profile.focus_areas[1]} 축을 중심으로 흐름을 읽는 편이 가장 정확합니다."
        )

    def _build_summary(self, analysis: MonthlyTransitAnalysis, profile: NatalProfile) -> str:
        if analysis.total_score >= 6:
            stance = "밀어붙일 타이밍과 정리할 타이밍이 분명해지는 달"
        elif analysis.total_score >= 0:
            stance = "작은 조정이 실제 성과로 이어지기 쉬운 달"
        elif analysis.intensity_score >= 8:
            stance = "리듬 관리와 우선순위 조정이 특히 중요한 달"
        else:
            stance = "무리한 확장보다 균형 회복이 먼저인 달"

        return (
            f"{analysis.month}월은 {analysis.top_theme_label} 이슈가 가장 크게 떠오르며, "
            f"{profile.focus_areas[0]} 성향이 배경에서 계속 작동합니다. "
            f"전체적으로는 {stance}입니다."
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
        evidence_text = strongest_evidence.headline if strongest_evidence is not None else "큰 파동은 제한적"

        if score >= 4:
            tone = "확장 쪽으로 흐름이 기울어 있습니다"
        elif score >= 0:
            tone = "천천히 정리하면 성과를 낼 수 있습니다"
        elif score <= -4:
            tone = "속도를 줄이고 방어적으로 움직이는 편이 좋습니다"
        else:
            tone = "조율이 필요하지만 충분히 다룰 수 있는 수준입니다"

        if theme_key == "career":
            guidance = "한 번에 많은 일을 벌이기보다 핵심 우선순위 하나를 끝까지 밀어보세요."
        elif theme_key == "money":
            guidance = "지출 구조를 먼저 정리하고, 큰 결정은 좋은 날짜 쪽으로 맞추는 편이 유리합니다."
        elif theme_key == "love":
            guidance = "상대의 반응을 추측하기보다 직접적인 대화와 리듬 조절이 도움이 됩니다."
        else:
            guidance = "피로 누적과 일정 과밀이 리스크를 키우므로 휴식과 마감 간격을 남겨두는 편이 좋습니다."

        return f"{focus} 영역은 {tone} 근거로는 {evidence_text} 흐름이 두드러지고, {guidance}"

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
            label = f"{theme_label} 운이 트이는 날"
            reason = (
                source_event.detail
                if source_event is not None
                else f"{theme_label} 관련 선택을 밀어붙이기 좋은 비교적 부드러운 흐름입니다."
            )
        else:
            label = f"{theme_label} 속도 조절이 필요한 날"
            reason = (
                source_event.detail
                if source_event is not None
                else f"{theme_label} 관련 압박이 높아져 무리한 결정을 피하는 편이 좋습니다."
            )

        return HoroscopeDateInsight(date=day.date, label=label, reason=reason)
