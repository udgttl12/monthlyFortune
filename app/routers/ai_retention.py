from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.schemas.ai_retention import (
    ActionCalendarRequest,
    ActionCalendarResponse,
    CoachRequest,
    CoachResponse,
    DailyBriefRequest,
    DailyBriefResponse,
)
from app.services.ai_retention_service import AIRetentionService
from app.services.astrology_service import AstrologyService
from app.services.cache import TTLCache
from app.services.chart_engine import ChartEngine
from app.services.geocoding_service import GeocodingService, LocationResolutionError
from app.services.llm_retention_client import LLMRetentionClient
from app.services.natal_chart_engine import NatalChartEngine
from app.services.timing_signal_service import TimingSignalService
from app.services.transit_engine import TransitEngine

router = APIRouter(prefix="/api/ai-retention", tags=["ai-retention"])

natal_chart_engine = NatalChartEngine()
geocoding_service = GeocodingService(cache=TTLCache(ttl_seconds=7 * 24 * 60 * 60))
astrology_service = AstrologyService(
    natal_chart_engine=natal_chart_engine,
    geocoding_service=geocoding_service,
    cache=TTLCache(ttl_seconds=24 * 60 * 60),
)
ai_retention_service = AIRetentionService(
    astrology_service=astrology_service,
    chart_engine=ChartEngine(),
    transit_engine=TransitEngine(natal_chart_engine=natal_chart_engine),
    timing_signal_service=TimingSignalService(),
    calendar_cache=TTLCache(ttl_seconds=7 * 24 * 60 * 60),
    daily_cache=TTLCache(ttl_seconds=24 * 60 * 60),
    coach_cache=TTLCache(ttl_seconds=24 * 60 * 60),
    llm_client=LLMRetentionClient.from_env(),
)


@router.get("/action-calendar", response_model=ActionCalendarResponse)
def get_action_calendar(
    birth_date: Optional[str] = Query(None, alias="birthDate"),
    birth_time: Optional[str] = Query(None, alias="birthTime"),
    city: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, alias="countryCode"),
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    timezone: Optional[str] = Query(None),
) -> ActionCalendarResponse:
    try:
        request = ActionCalendarRequest(
            birthDate=birth_date,
            birthTime=birth_time,
            city=city,
            countryCode=country_code,
            timezone=timezone,
            year=year,
            month=month,
        )
        return ai_retention_service.action_calendar(request)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc
    except LocationResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/daily-brief", response_model=DailyBriefResponse)
def get_daily_brief(
    birth_date: Optional[str] = Query(None, alias="birthDate"),
    birth_time: Optional[str] = Query(None, alias="birthTime"),
    city: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, alias="countryCode"),
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    target_date: Optional[date] = Query(None, alias="targetDate"),
    timezone: Optional[str] = Query(None),
) -> DailyBriefResponse:
    try:
        request = DailyBriefRequest(
            birthDate=birth_date,
            birthTime=birth_time,
            city=city,
            countryCode=country_code,
            timezone=timezone,
            year=year,
            month=month,
            targetDate=target_date,
        )
        return ai_retention_service.daily_brief(request)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc
    except LocationResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/coach", response_model=CoachResponse)
def post_timing_coach(request: CoachRequest) -> CoachResponse:
    try:
        return ai_retention_service.timing_coach(request)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc
    except LocationResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
