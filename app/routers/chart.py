from fastapi import APIRouter, HTTPException, Query

from app.schemas.chart import NatalChartRequest, NatalChartResponse
from app.services.astrology_service import AstrologyService
from app.services.cache import TTLCache
from app.services.geocoding_service import GeocodingService, LocationResolutionError
from app.services.natal_chart_engine import NatalChartEngine

router = APIRouter(prefix="/api/chart", tags=["chart"])

astrology_service = AstrologyService(
    natal_chart_engine=NatalChartEngine(),
    geocoding_service=GeocodingService(cache=TTLCache(ttl_seconds=7 * 24 * 60 * 60)),
    cache=TTLCache(ttl_seconds=24 * 60 * 60),
)


@router.get("/natal", response_model=NatalChartResponse)
def get_natal_chart(
    birth_date: str = Query(..., alias="birthDate", description="YYYY-MM-DD"),
    birth_time: str = Query(..., alias="birthTime", description="HH:MM"),
    city: str = Query(...),
    country_code: str = Query(..., alias="countryCode"),
    timezone: str | None = Query(None),
) -> NatalChartResponse:
    try:
        request = NatalChartRequest(
            birthDate=birth_date,
            birthTime=birth_time,
            city=city,
            countryCode=country_code,
            timezone=timezone,
        )
        return astrology_service.build_natal_chart(request)
    except LocationResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
