from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class NatalChartRequest(CamelModel):
    birth_date: date = Field(alias="birthDate")
    birth_time: str = Field(alias="birthTime", pattern=r"^\d{2}:\d{2}$")
    city: str = Field(min_length=1)
    country_code: str = Field(alias="countryCode", min_length=2, max_length=2)
    timezone: str | None = None

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        city = value.strip()
        if not city:
            raise ValueError("city must not be blank")
        return city

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        timezone_name = value.strip()
        if not timezone_name:
            return None

        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc

        return timezone_name


class ChartPoint(CamelModel):
    name: str
    longitude: float
    sign: str
    degree: int
    minute: int
    retrograde: bool
    house: int | None = None


class ChartAngle(CamelModel):
    longitude: float
    sign: str
    degree: int
    minute: int


class ChartAngles(CamelModel):
    asc: ChartAngle
    mc: ChartAngle


class ChartHouse(CamelModel):
    house_number: int = Field(alias="houseNumber")
    sign: str
    cusp_longitude: float = Field(alias="cuspLongitude")


class ChartAspect(CamelModel):
    point_a: str = Field(alias="pointA")
    point_b: str = Field(alias="pointB")
    aspect: str
    orb: float
    applying: bool


class ResolvedLocation(CamelModel):
    resolved_name: str = Field(alias="resolvedName")
    latitude: float
    longitude: float
    timezone: str
    country_code: str = Field(alias="countryCode")


class NatalChartResponse(CamelModel):
    points: list[ChartPoint]
    angles: ChartAngles
    houses: list[ChartHouse]
    aspects: list[ChartAspect]
    location: ResolvedLocation
