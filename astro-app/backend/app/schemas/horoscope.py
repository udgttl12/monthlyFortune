from pydantic import BaseModel


class HoroscopeCards(BaseModel):
    career: str
    money: str
    love: str
    risk: str


class TransitEvent(BaseModel):
    date: str
    title: str
    impact: str


class MonthlyHoroscopeResponse(BaseModel):
    name: str
    year: int
    month: int
    cards: HoroscopeCards
    events: list[TransitEvent]
