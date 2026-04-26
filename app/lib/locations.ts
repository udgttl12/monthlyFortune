export interface CountryOption {
  code: string;
  label: string;
  defaultTimezone: string;
}

export interface LocationOption {
  city: string;
  countryCode: string;
  timezone: string;
  note: string;
}

export const COUNTRY_OPTIONS: CountryOption[] = [
  { code: "KR", label: "대한민국", defaultTimezone: "Asia/Seoul" },
  { code: "JP", label: "일본", defaultTimezone: "Asia/Tokyo" },
  { code: "US", label: "미국", defaultTimezone: "America/New_York" },
  { code: "CN", label: "중국", defaultTimezone: "Asia/Shanghai" },
  { code: "GB", label: "영국", defaultTimezone: "Europe/London" }
];

export const LOCATION_OPTIONS: LocationOption[] = [
  { city: "서울", countryCode: "KR", timezone: "Asia/Seoul", note: "수도권" },
  { city: "부산", countryCode: "KR", timezone: "Asia/Seoul", note: "영남권" },
  { city: "인천", countryCode: "KR", timezone: "Asia/Seoul", note: "수도권" },
  { city: "대구", countryCode: "KR", timezone: "Asia/Seoul", note: "영남권" },
  { city: "대전", countryCode: "KR", timezone: "Asia/Seoul", note: "충청권" },
  { city: "광주", countryCode: "KR", timezone: "Asia/Seoul", note: "호남권" },
  { city: "수원", countryCode: "KR", timezone: "Asia/Seoul", note: "경기 남부" },
  { city: "제주", countryCode: "KR", timezone: "Asia/Seoul", note: "제주권" },
  { city: "도쿄", countryCode: "JP", timezone: "Asia/Tokyo", note: "간토" },
  { city: "오사카", countryCode: "JP", timezone: "Asia/Tokyo", note: "간사이" },
  { city: "뉴욕", countryCode: "US", timezone: "America/New_York", note: "미국 동부" },
  { city: "로스앤젤레스", countryCode: "US", timezone: "America/Los_Angeles", note: "미국 서부" },
  { city: "시카고", countryCode: "US", timezone: "America/Chicago", note: "미국 중부" },
  { city: "상하이", countryCode: "CN", timezone: "Asia/Shanghai", note: "화동" },
  { city: "베이징", countryCode: "CN", timezone: "Asia/Shanghai", note: "화북" },
  { city: "런던", countryCode: "GB", timezone: "Europe/London", note: "잉글랜드" }
];

export function getCountryLabel(countryCode?: string): string {
  return COUNTRY_OPTIONS.find((country) => country.code === countryCode)?.label ?? "미정";
}

export function getDefaultTimezone(countryCode?: string): string {
  return COUNTRY_OPTIONS.find((country) => country.code === countryCode)?.defaultTimezone ?? "Asia/Seoul";
}

export function getCitiesByCountry(countryCode?: string): LocationOption[] {
  return LOCATION_OPTIONS.filter((option) => option.countryCode === countryCode);
}

export function getLocationOption(city?: string, countryCode?: string): LocationOption | undefined {
  if (!city || !countryCode) {
    return undefined;
  }

  return LOCATION_OPTIONS.find(
    (option) => option.countryCode === countryCode && option.city.trim() === city.trim()
  );
}
