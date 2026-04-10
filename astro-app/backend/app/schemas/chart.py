from datetime import date

from pydantic import BaseModel, Field


class ChartRequest(BaseModel):
    name: str
    birth_date: date
    birth_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    latitude: float
    longitude: float
    timezone: str = "UTC"


class Planet(BaseModel):
    name: str
    longitude: float


class House(BaseModel):
    house: int
    cusp: float


class Aspect(BaseModel):
    between: str
    aspect: str
    orb: float


class ChartResponse(BaseModel):
    name: str
    planets: list[Planet]
    houses: list[House]
    aspects: list[Aspect]
