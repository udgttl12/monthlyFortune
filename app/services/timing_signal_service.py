from datetime import date

from app.schemas.ai_retention import ActionCalendarDay, DailyBriefResponse, TimingSignal
from app.services.transit_engine import DailyTransitScore, MonthlyTransitAnalysis


class TimingSignalService:
    def build_daily_signal(self, day: DailyTransitScore) -> TimingSignal:
        return TimingSignal(
            date=day.date,
            totalScore=day.total_score,
            categoryScores=day.category_scores,
            positiveSignals=[event.headline for event in day.positive_events],
            negativeSignals=[event.headline for event in day.negative_events],
        )

    def build_month_signals(self, analysis: MonthlyTransitAnalysis) -> list[TimingSignal]:
        return [self.build_daily_signal(day) for day in analysis.daily_scores]

    def find_day(self, analysis: MonthlyTransitAnalysis, target_date: date) -> DailyTransitScore:
        for day in analysis.daily_scores:
            if day.date == target_date:
                return day

        return min(analysis.daily_scores, key=lambda day: abs(day.date.toordinal() - target_date.toordinal()))

    def build_fallback_calendar_day(self, day: DailyTransitScore) -> ActionCalendarDay:
        category = max(day.category_scores, key=lambda key: abs(day.category_scores[key]))
        tone = self._tone_for_score(day.total_score)
        return ActionCalendarDay(
            date=day.date,
            score=self._score_for_total(day.total_score),
            tone=tone,
            title=self._title_for_tone(tone),
            action=self._action_for_category(category, tone),
            avoid=self._avoid_for_category(category),
            reason=self._best_reason(day),
            categories=[category],
        )

    def build_fallback_daily_brief(self, day: DailyTransitScore) -> DailyBriefResponse:
        calendar_day = self.build_fallback_calendar_day(day)
        return DailyBriefResponse(
            date=day.date,
            score=calendar_day.score,
            tone=calendar_day.tone,
            headline=calendar_day.title,
            summary=calendar_day.reason,
            bestTimeHint="오전에는 정리와 준비, 오후에는 실행과 연락에 무게를 둡니다.",
            avoidTimeHint="감정이 앞서는 순간에는 바로 답하지 말고 한 번 더 확인합니다.",
            action=calendar_day.action,
            avoid=calendar_day.avoid,
            reflectionPrompt="오늘의 선택 중 다시 반복하고 싶은 장면은 무엇이었나요?",
            llmEnhanced=False,
        )

    def _score_for_total(self, total_score: float) -> int:
        return max(1, min(10, round(5 + total_score)))

    def _tone_for_score(self, total_score: float) -> str:
        if total_score >= 1.0:
            return "supportive"
        if total_score <= -1.0:
            return "challenging"
        return "neutral"

    def _title_for_tone(self, tone: str) -> str:
        if tone == "supportive":
            return "움직임을 만들기 좋은 날"
        if tone == "challenging":
            return "속도를 낮추면 손실을 줄이는 날"
        return "작게 정리하고 균형을 맞추는 날"

    def _best_reason(self, day: DailyTransitScore) -> str:
        events = day.positive_events if day.total_score >= 0 else day.negative_events
        if events:
            return events[0].headline
        return "큰 파동은 제한적이므로 일상의 리듬을 지키는 것이 중요합니다."

    def _action_for_category(self, category: str, tone: str) -> str:
        if category == "career":
            return "중요한 업무는 먼저 구조를 잡고 짧게 공유합니다."
        if category == "money":
            return "예산과 결제 조건을 숫자로 확인합니다."
        if category == "love":
            return "상대에게 필요한 말을 짧고 분명하게 전합니다."
        return "일정을 줄이고 회복 시간을 확보합니다."

    def _avoid_for_category(self, category: str) -> str:
        if category == "career":
            return "확인되지 않은 약속을 성급하게 확정하지 않습니다."
        if category == "money":
            return "큰 지출과 충동 구매를 같은 날 결정하지 않습니다."
        if category == "love":
            return "감정이 올라온 상태에서 긴 메시지를 보내지 않습니다."
        return "몸의 신호를 무시한 무리한 약속을 피합니다."
