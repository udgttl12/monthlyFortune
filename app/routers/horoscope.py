from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.schemas.horoscope import (
    MonthlyHoroscopeRequest,
    MonthlyHoroscopeResponse,
    YearlyHoroscopeRequest,
    YearlyHoroscopeResponse,
)
from app.services.astrology_service import AstrologyService
from app.services.cache import TTLCache
from app.services.chart_engine import ChartEngine
from app.services.geocoding_service import GeocodingService, LocationResolutionError
from app.services.horoscope_service import HoroscopeService
from app.services.interpretation_engine import InterpretationEngine
from app.services.natal_chart_engine import NatalChartEngine
from app.services.persistent_cache import PersistentCache
from app.services.transit_engine import TransitEngine
from app.services.xai_service import MonthlyReportClient

router = APIRouter(prefix="/api/horoscope", tags=["horoscope"])

natal_chart_engine = NatalChartEngine()
geocoding_service = GeocodingService(cache=TTLCache(ttl_seconds=7 * 24 * 60 * 60))
astrology_service = AstrologyService(
    natal_chart_engine=natal_chart_engine,
    geocoding_service=geocoding_service,
    cache=TTLCache(ttl_seconds=24 * 60 * 60),
)
horoscope_service = HoroscopeService(
    astrology_service=astrology_service,
    chart_engine=ChartEngine(),
    transit_engine=TransitEngine(natal_chart_engine=natal_chart_engine),
    interpretation_engine=InterpretationEngine(),
    yearly_cache=TTLCache(ttl_seconds=24 * 60 * 60),
    monthly_cache=TTLCache(ttl_seconds=7 * 24 * 60 * 60),
    analysis_cache=TTLCache(ttl_seconds=7 * 24 * 60 * 60),
    xai_service=MonthlyReportClient.from_env(),
    persistent_cache=PersistentCache.from_env(),
)


@router.get("/yearly", response_model=YearlyHoroscopeResponse)
def get_yearly_horoscope(
    birth_date: Optional[str] = Query(None, alias="birthDate"),
    birth_time: Optional[str] = Query(None, alias="birthTime"),
    city: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, alias="countryCode"),
    year: Optional[str] = Query(None),
    timezone: Optional[str] = Query(None),
) -> YearlyHoroscopeResponse:
    try:
        request = YearlyHoroscopeRequest(
            birthDate=birth_date,
            birthTime=birth_time,
            city=city,
            countryCode=country_code,
            timezone=timezone,
            year=year,
        )
        return horoscope_service.yearly_horoscope(request)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc
    except LocationResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/monthly", response_model=MonthlyHoroscopeResponse)
def get_monthly_horoscope(
    birth_date: Optional[str] = Query(None, alias="birthDate"),
    birth_time: Optional[str] = Query(None, alias="birthTime"),
    city: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, alias="countryCode"),
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    timezone: Optional[str] = Query(None),
) -> MonthlyHoroscopeResponse:
    try:
        request = MonthlyHoroscopeRequest(
            birthDate=birth_date,
            birthTime=birth_time,
            city=city,
            countryCode=country_code,
            timezone=timezone,
            year=year,
            month=month,
        )
        return horoscope_service.monthly_horoscope(request)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc
    except LocationResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
