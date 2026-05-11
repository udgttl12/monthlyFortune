from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.chart import CamelModel
from app.schemas.horoscope import MonthlyHoroscopeRequest

TimingTone = Literal["supportive", "neutral", "challenging"]
TimingCategory = Literal["career", "money", "love", "risk"]


class ActionCalendarRequest(MonthlyHoroscopeRequest):
    pass


class DailyBriefRequest(MonthlyHoroscopeRequest):
    target_date: date = Field(alias="targetDate")


class CoachRequest(MonthlyHoroscopeRequest):
    question: str = Field(min_length=4, max_length=500)


class TimingSignal(CamelModel):
    date: date
    total_score: float = Field(alias="totalScore")
    category_scores: dict[str, float] = Field(alias="categoryScores")
    positive_signals: list[str] = Field(alias="positiveSignals")
    negative_signals: list[str] = Field(alias="negativeSignals")


class ActionCalendarDay(CamelModel):
    date: date
    score: int = Field(ge=1, le=10)
    tone: TimingTone
    title: str
    action: str
    avoid: str
    reason: str
    categories: list[TimingCategory]


class ActionCalendarResponse(CamelModel):
    year: int
    month: int
    profile_summary: str = Field(alias="profileSummary")
    llm_enhanced: bool = Field(alias="llmEnhanced")
    days: list[ActionCalendarDay]


class DailyBriefResponse(CamelModel):
    date: date
    score: int = Field(ge=1, le=10)
    tone: TimingTone
    headline: str
    summary: str
    best_time_hint: str = Field(alias="bestTimeHint")
    avoid_time_hint: str = Field(alias="avoidTimeHint")
    action: str
    avoid: str
    reflection_prompt: str = Field(alias="reflectionPrompt")
    llm_enhanced: bool = Field(alias="llmEnhanced")


class CoachRecommendedDate(CamelModel):
    date: date
    label: str
    reason: str


class CoachResponse(CamelModel):
    question: str
    answer: str
    recommended_dates: list[CoachRecommendedDate] = Field(alias="recommendedDates")
    caution_dates: list[CoachRecommendedDate] = Field(alias="cautionDates")
    first_action: str = Field(alias="firstAction")
    message_draft: str = Field(alias="messageDraft")
    reasoning_summary: str = Field(alias="reasoningSummary")
    disclaimer: str
    llm_enhanced: bool = Field(alias="llmEnhanced")


class ActionCalendarLLMResponse(CamelModel):
    days: list[ActionCalendarDay]


class DailyBriefLLMResponse(CamelModel):
    headline: str
    summary: str
    best_time_hint: str = Field(alias="bestTimeHint")
    avoid_time_hint: str = Field(alias="avoidTimeHint")
    action: str
    avoid: str
    reflection_prompt: str = Field(alias="reflectionPrompt")


class CoachLLMResponse(CamelModel):
    answer: str
    recommended_dates: list[CoachRecommendedDate] = Field(alias="recommendedDates")
    caution_dates: list[CoachRecommendedDate] = Field(alias="cautionDates")
    first_action: str = Field(alias="firstAction")
    message_draft: str = Field(alias="messageDraft")
    reasoning_summary: str = Field(alias="reasoningSummary")
    disclaimer: str
