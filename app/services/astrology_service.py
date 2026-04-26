from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.chart import NatalChartRequest, NatalChartResponse, ResolvedLocation
from app.services.cache import TTLCache
from app.services.geocoding_service import GeocodingService
from app.services.natal_chart_engine import NatalChartEngine


@dataclass(frozen=True)
class BirthChartContext:
    request: NatalChartRequest
    birth_dt_local: datetime
    natal_chart: NatalChartResponse
    location: ResolvedLocation


class AstrologyService:
    def __init__(
        self,
        natal_chart_engine: NatalChartEngine,
        geocoding_service: GeocodingService,
        cache: TTLCache | None = None,
    ) -> None:
        self.natal_chart_engine = natal_chart_engine
        self.geocoding_service = geocoding_service
        self.cache = cache or TTLCache(ttl_seconds=24 * 60 * 60)

    def build_natal_chart(self, request: NatalChartRequest) -> NatalChartResponse:
        return self.build_birth_context(request).natal_chart

    def build_birth_context(self, request: NatalChartRequest) -> BirthChartContext:
        resolved_location = self.geocoding_service.resolve(
            city=request.city,
            country_code=request.country_code,
            timezone_override=request.timezone,
        )

        cache_key = ":".join(
            [
                request.birth_date.isoformat(),
                request.birth_time,
                request.city.casefold(),
                request.country_code,
                resolved_location.timezone,
            ]
        )
        hour, minute = map(int, request.birth_time.split(":"))
        birth_dt_local = datetime(
            request.birth_date.year,
            request.birth_date.month,
            request.birth_date.day,
            hour,
            minute,
            tzinfo=ZoneInfo(resolved_location.timezone),
        )

        cached = self.cache.get(cache_key)
        if cached is not None:
            natal_chart = NatalChartResponse(**cached)
            return BirthChartContext(
                request=request,
                birth_dt_local=birth_dt_local,
                natal_chart=natal_chart,
                location=natal_chart.location,
            )

        chart_data = self.natal_chart_engine.calculate_chart(
            birth_dt_local=birth_dt_local,
            latitude=resolved_location.latitude,
            longitude=resolved_location.longitude,
        )
        response = NatalChartResponse(
            points=chart_data["points"],
            angles=chart_data["angles"],
            houses=chart_data["houses"],
            aspects=chart_data["aspects"],
            location=ResolvedLocation(
                resolvedName=resolved_location.resolved_name,
                latitude=resolved_location.latitude,
                longitude=resolved_location.longitude,
                timezone=resolved_location.timezone,
                countryCode=resolved_location.country_code,
            ),
        )
        self.cache.set(cache_key, response.model_dump(by_alias=True))
        return BirthChartContext(
            request=request,
            birth_dt_local=birth_dt_local,
            natal_chart=response,
            location=response.location,
        )
