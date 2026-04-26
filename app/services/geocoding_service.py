from dataclasses import dataclass
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from timezonefinder import TimezoneFinder

from app.services.cache import TTLCache

NOMINATIM_URL: Final = "https://nominatim.openstreetmap.org/search"
USER_AGENT: Final = "monthly-fortune/1.0 (astrology chart resolver)"


class LocationResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedLocation:
    resolved_name: str
    latitude: float
    longitude: float
    timezone: str
    country_code: str


def _normalize_city(value: str) -> str:
    return " ".join(value.strip().casefold().replace(",", " ").split())


KNOWN_LOCATION_OVERRIDES: Final[dict[tuple[str, str], ResolvedLocation]] = {
    ("KR", "busan"): ResolvedLocation("Busan, South Korea", 35.1796, 129.0756, "Asia/Seoul", "KR"),
    ("KR", "busan-si"): ResolvedLocation("Busan, South Korea", 35.1796, 129.0756, "Asia/Seoul", "KR"),
    ("KR", "부산"): ResolvedLocation("Busan, South Korea", 35.1796, 129.0756, "Asia/Seoul", "KR"),
    ("KR", "seoul"): ResolvedLocation("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul", "KR"),
    ("KR", "서울"): ResolvedLocation("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul", "KR"),
    ("KR", "incheon"): ResolvedLocation("Incheon, South Korea", 37.4563, 126.7052, "Asia/Seoul", "KR"),
    ("KR", "인천"): ResolvedLocation("Incheon, South Korea", 37.4563, 126.7052, "Asia/Seoul", "KR"),
    ("KR", "daegu"): ResolvedLocation("Daegu, South Korea", 35.8714, 128.6014, "Asia/Seoul", "KR"),
    ("KR", "대구"): ResolvedLocation("Daegu, South Korea", 35.8714, 128.6014, "Asia/Seoul", "KR"),
    ("KR", "daejeon"): ResolvedLocation("Daejeon, South Korea", 36.3504, 127.3845, "Asia/Seoul", "KR"),
    ("KR", "대전"): ResolvedLocation("Daejeon, South Korea", 36.3504, 127.3845, "Asia/Seoul", "KR"),
    ("KR", "gwangju"): ResolvedLocation("Gwangju, South Korea", 35.1595, 126.8526, "Asia/Seoul", "KR"),
    ("KR", "광주"): ResolvedLocation("Gwangju, South Korea", 35.1595, 126.8526, "Asia/Seoul", "KR"),
    ("KR", "ulsan"): ResolvedLocation("Ulsan, South Korea", 35.5384, 129.3114, "Asia/Seoul", "KR"),
    ("KR", "울산"): ResolvedLocation("Ulsan, South Korea", 35.5384, 129.3114, "Asia/Seoul", "KR"),
    ("KR", "jeju"): ResolvedLocation("Jeju, South Korea", 33.4996, 126.5312, "Asia/Seoul", "KR"),
    ("KR", "제주"): ResolvedLocation("Jeju, South Korea", 33.4996, 126.5312, "Asia/Seoul", "KR"),
    ("KR", "gangneung"): ResolvedLocation("Gangneung, South Korea", 37.7519, 128.8761, "Asia/Seoul", "KR"),
    ("KR", "강릉"): ResolvedLocation("Gangneung, South Korea", 37.7519, 128.8761, "Asia/Seoul", "KR"),
    ("KR", "jeonju"): ResolvedLocation("Jeonju, South Korea", 35.8242, 127.1480, "Asia/Seoul", "KR"),
    ("KR", "전주"): ResolvedLocation("Jeonju, South Korea", 35.8242, 127.1480, "Asia/Seoul", "KR"),
}


class GeocodingService:
    def __init__(self, cache: TTLCache | None = None) -> None:
        self.cache = cache or TTLCache(ttl_seconds=7 * 24 * 60 * 60)
        self.timezone_finder = TimezoneFinder()

    def resolve(self, city: str, country_code: str, timezone_override: str | None = None) -> ResolvedLocation:
        normalized_country = country_code.strip().upper()
        normalized_city = _normalize_city(city)
        cache_key = f"{normalized_country}:{normalized_city}:{timezone_override or ''}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return ResolvedLocation(**cached)

        resolved = self._resolve_known_location(normalized_country, normalized_city)
        if resolved is None:
            resolved = self._resolve_via_nominatim(city=city, country_code=normalized_country)

        timezone_name = timezone_override or resolved.timezone or self._infer_timezone(resolved.latitude, resolved.longitude)
        timezone_name = self._validate_timezone(timezone_name)
        final_location = ResolvedLocation(
            resolved_name=resolved.resolved_name,
            latitude=resolved.latitude,
            longitude=resolved.longitude,
            timezone=timezone_name,
            country_code=resolved.country_code,
        )
        self.cache.set(cache_key, final_location.__dict__)
        return final_location

    def _resolve_known_location(self, country_code: str, normalized_city: str) -> ResolvedLocation | None:
        return KNOWN_LOCATION_OVERRIDES.get((country_code, normalized_city))

    def _resolve_via_nominatim(self, city: str, country_code: str) -> ResolvedLocation:
        params = {
            "q": city,
            "countrycodes": country_code.lower(),
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "ko,en"}

        try:
            response = httpx.get(NOMINATIM_URL, params=params, headers=headers, timeout=10.0, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LocationResolutionError("Failed to contact geocoding service") from exc

        payload = response.json()
        if not payload:
            raise LocationResolutionError(f"Could not resolve city '{city}' in country '{country_code}'")

        result = payload[0]
        try:
            latitude = float(result["lat"])
            longitude = float(result["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LocationResolutionError("Geocoding service returned invalid coordinates") from exc

        display_name = result.get("display_name") or f"{city}, {country_code}"
        return ResolvedLocation(
            resolved_name=display_name,
            latitude=latitude,
            longitude=longitude,
            timezone="",
            country_code=country_code,
        )

    def _infer_timezone(self, latitude: float, longitude: float) -> str:
        timezone_name = self.timezone_finder.timezone_at(lng=longitude, lat=latitude)
        if timezone_name is None:
            timezone_name = self.timezone_finder.certain_timezone_at(lng=longitude, lat=latitude)

        if timezone_name is None:
            raise LocationResolutionError("Could not infer timezone from coordinates")

        return timezone_name

    def _validate_timezone(self, timezone_name: str) -> str:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise LocationResolutionError(f"Invalid timezone '{timezone_name}'") from exc

        return timezone_name
