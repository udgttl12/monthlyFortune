import type { Route } from "next";

export interface HoroscopeSearchParams {
  birthDate?: string;
  birthTime?: string;
  city?: string;
  country?: string;
  timezone?: string;
  year?: string;
  month?: string;
  timeUnknown?: string;
}

export interface HoroscopeWindow {
  startDate: string;
  endDate: string;
  label: string;
}

export interface YearlyHoroscopeMonth {
  month: number;
  title: string;
  focusAreas: string[];
  intensityScore: number;
  topTheme: string;
  luckyWindow: HoroscopeWindow;
  cautionWindow: HoroscopeWindow;
}

export interface YearlyHoroscopeResponse {
  year: number;
  profileSummary: string;
  months: YearlyHoroscopeMonth[];
}

export interface HoroscopeSectionSet {
  career: string;
  money: string;
  love: string;
  risk: string;
}

export interface HoroscopeDateInsight {
  date: string;
  label: string;
  reason: string;
}

export interface HoroscopeEvidence {
  date: string;
  headline: string;
  detail: string;
  tone: "supportive" | "challenging";
}

export interface MonthlyHoroscopeResponse {
  year: number;
  month: number;
  summary: string;
  sections: HoroscopeSectionSet;
  luckyDates: HoroscopeDateInsight[];
  cautionDates: HoroscopeDateInsight[];
  evidence: HoroscopeEvidence[];
  llmEnhanced: boolean;
}

export function hasRequiredBirthDetails(searchParams: HoroscopeSearchParams): boolean {
  return Boolean(
    searchParams.birthDate &&
      searchParams.birthTime &&
      searchParams.city &&
      searchParams.country
  );
}

export function getSelectedHoroscopeYear(
  searchParams: HoroscopeSearchParams,
  referenceDate: Date = new Date()
): number {
  const rawYear = Number(searchParams.year);
  if (Number.isInteger(rawYear) && rawYear >= 1900 && rawYear <= 2100) {
    return rawYear;
  }

  return referenceDate.getFullYear();
}

export function getSelectedHoroscopeMonth(
  selectedYear: number,
  requestedMonth?: string,
  referenceDate: Date = new Date()
): number {
  const parsedMonth = Number(requestedMonth);
  if (Number.isInteger(parsedMonth) && parsedMonth >= 1 && parsedMonth <= 12) {
    return parsedMonth;
  }

  if (selectedYear === referenceDate.getFullYear()) {
    return referenceDate.getMonth() + 1;
  }

  return 1;
}

export function buildHoroscopeApiParams(
  searchParams: HoroscopeSearchParams,
  selectedYear: number,
  selectedMonth?: number
): URLSearchParams {
  const params = new URLSearchParams({
    birthDate: searchParams.birthDate ?? "",
    birthTime: searchParams.birthTime ?? "",
    city: searchParams.city ?? "",
    countryCode: searchParams.country ?? "",
    year: String(selectedYear)
  });

  if (selectedMonth !== undefined) {
    params.set("month", String(selectedMonth));
  }

  if (searchParams.timezone) {
    params.set("timezone", searchParams.timezone);
  }

  return params;
}

export function buildHoroscopePageHref(
  searchParams: HoroscopeSearchParams,
  selectedYear: number,
  selectedMonth: number
): Route {
  const params = new URLSearchParams({
    birthDate: searchParams.birthDate ?? "",
    birthTime: searchParams.birthTime ?? "",
    city: searchParams.city ?? "",
    country: searchParams.country ?? "",
    year: String(selectedYear),
    month: String(selectedMonth),
    timeUnknown: searchParams.timeUnknown ?? "false"
  });

  if (searchParams.timezone) {
    params.set("timezone", searchParams.timezone);
  }

  return `/horoscope?${params.toString()}` as Route;
}

export function formatHoroscopeDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  return `${date.getMonth() + 1}월 ${date.getDate()}일`;
}
