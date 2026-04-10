from datetime import date

from fastapi import APIRouter, Query

from app.schemas.chart import ChartRequest, ChartResponse
from app.schemas.horoscope import MonthlyHoroscopeResponse
from app.services.astrology_service import AstrologyService

router = APIRouter()
service = AstrologyService()


@router.get("/chart", response_model=ChartResponse)
def get_chart(
    name: str = Query(...),
    birth_date: date = Query(..., description="YYYY-MM-DD"),
    birth_time: str = Query(..., description="HH:MM"),
    latitude: float = Query(...),
    longitude: float = Query(...),
    timezone: str = Query("UTC"),
) -> ChartResponse:
    request = ChartRequest(
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )
    return service.build_chart(request)


@router.get("/horoscope/monthly", response_model=MonthlyHoroscopeResponse)
def get_monthly_horoscope(
    name: str = Query(...),
    birth_date: date = Query(..., description="YYYY-MM-DD"),
    birth_time: str = Query(..., description="HH:MM"),
    latitude: float = Query(...),
    longitude: float = Query(...),
    timezone: str = Query("UTC"),
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> MonthlyHoroscopeResponse:
    request = ChartRequest(
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )
    return service.build_monthly_horoscope(request=request, year=year, month=month)
