from fastapi import APIRouter, Query

from app.schemas.horoscope import MonthlyHoroscopeResponse
from app.services.cache import TTLCache
from app.services.chart_engine import ChartEngine
from app.services.horoscope_service import HoroscopeService
from app.services.interpretation_engine import InterpretationEngine
from app.services.transit_engine import TransitEngine

router = APIRouter(prefix="/api/horoscope", tags=["horoscope"])

horoscope_service = HoroscopeService(
    chart_engine=ChartEngine(),
    transit_engine=TransitEngine(),
    interpretation_engine=InterpretationEngine(),
    cache=TTLCache(ttl_seconds=3600),
)


@router.get("/monthly", response_model=MonthlyHoroscopeResponse)
def get_monthly_horoscope(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> MonthlyHoroscopeResponse:
    return horoscope_service.monthly_horoscope(year=year, month=month)
