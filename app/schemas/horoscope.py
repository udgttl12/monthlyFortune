from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.chart import CamelModel, NatalChartRequest


class YearlyHoroscopeRequest(NatalChartRequest):
    year: int = Field(ge=1900, le=2100)


class MonthlyHoroscopeRequest(YearlyHoroscopeRequest):
    month: int = Field(ge=1, le=12)


class HoroscopeWindow(CamelModel):
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    label: str


class YearlyMonthOverview(CamelModel):
    month: int
    title: str
    focus_areas: list[str] = Field(alias="focusAreas")
    intensity_score: int = Field(alias="intensityScore")
    top_theme: str = Field(alias="topTheme")
    lucky_window: HoroscopeWindow = Field(alias="luckyWindow")
    caution_window: HoroscopeWindow = Field(alias="cautionWindow")


class YearlyHoroscopeResponse(CamelModel):
    year: int
    profile_summary: str = Field(alias="profileSummary")
    months: list[YearlyMonthOverview]


class HoroscopeSections(CamelModel):
    career: str
    money: str
    love: str
    risk: str


class HoroscopeDateInsight(CamelModel):
    date: date
    label: str
    reason: str


class HoroscopeEvidence(CamelModel):
    date: date
    headline: str
    detail: str
    tone: Literal["supportive", "challenging"]


class MonthlyHoroscopeResponse(CamelModel):
    year: int
    month: int
    summary: str
    sections: HoroscopeSections
    lucky_dates: list[HoroscopeDateInsight] = Field(alias="luckyDates")
    caution_dates: list[HoroscopeDateInsight] = Field(alias="cautionDates")
    evidence: list[HoroscopeEvidence]
    llm_enhanced: bool = Field(alias="llmEnhanced")


class MonthlyHoroscopeLLMDateInsight(CamelModel):
    label: str
    reason: str


class MonthlyHoroscopeLLMEvidence(CamelModel):
    headline: str
    detail: str


class MonthlyHoroscopeLLMResponse(CamelModel):
    summary: str
    sections: HoroscopeSections
    lucky_dates: list[MonthlyHoroscopeLLMDateInsight] = Field(alias="luckyDates")
    caution_dates: list[MonthlyHoroscopeLLMDateInsight] = Field(alias="cautionDates")
    evidence: list[MonthlyHoroscopeLLMEvidence]
