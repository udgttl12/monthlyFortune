import type { Route } from "next";
import {
  buildCalendarPageHref,
  buildCoachPageHref,
  buildTodayPageHref,
  getTodayInKorea
} from "@/app/lib/aiRetention";
import {
  HoroscopeSearchParams,
  buildHoroscopePageHref
} from "@/app/lib/horoscope";
import type { LastViewedBirthDetails } from "@/app/lib/birthDetailsStorage";
import { parseBirthDateInput } from "@/app/lib/birthDateInput";
import { parseBirthTimeInput } from "@/app/lib/birthTimeInput";
import { getDefaultTimezone, getLocationOption } from "@/app/lib/locations";

export type FloatingMenuPage = "home" | "chart" | "horoscope" | "retention";
export type FloatingMenuAction = "copy" | "top" | "recent";

export interface FloatingMenuItem {
  label: string;
  action?: FloatingMenuAction;
  href?: Route;
}

interface FloatingMenuOptions {
  page: FloatingMenuPage;
  searchParams?: HoroscopeSearchParams;
  hasCopyText?: boolean;
  selectedYear?: number;
  selectedMonth?: number;
}

interface AdjacentMonth {
  year: number;
  month: number;
}

export function getAdjacentHoroscopeMonths(year: number, month: number): {
  previous: AdjacentMonth;
  next: AdjacentMonth;
} {
  return {
    previous: month === 1 ? { year: year - 1, month: 12 } : { year, month: month - 1 },
    next: month === 12 ? { year: year + 1, month: 1 } : { year, month: month + 1 }
  };
}

function buildChartPageHref(searchParams: HoroscopeSearchParams = {}): Route {
  const params = new URLSearchParams({
    birthDate: searchParams.birthDate ?? "",
    birthTime: searchParams.birthTime ?? "",
    city: searchParams.city ?? "",
    country: searchParams.country ?? "",
    timeUnknown: searchParams.timeUnknown ?? "false"
  });

  if (searchParams.timezone) {
    params.set("timezone", searchParams.timezone);
  }

  return `/chart?${params.toString()}` as Route;
}

function buildHoroscopeHref(
  searchParams: HoroscopeSearchParams = {},
  year = new Date().getFullYear(),
  month?: number
): Route {
  return buildHoroscopePageHref(searchParams, year, month ?? (Number(searchParams.month) || 1));
}

export function buildStoredBirthDetailsHref(
  details: LastViewedBirthDetails,
  target: "chart" | "horoscope"
): Route {
  const birthDate = parseBirthDateInput(details.birthDateInput) ?? "";
  const parsedBirthTime = parseBirthTimeInput(details.birthTimeInput);
  const birthTime = details.timeUnknown ? "12:00" : parsedBirthTime ?? "";
  const location = getLocationOption(details.city, details.country);
  const timezone = location?.timezone ?? getDefaultTimezone(details.country);
  const params = new URLSearchParams({
    birthDate,
    birthTime,
    city: details.city,
    country: details.country,
    timeUnknown: details.timeUnknown ? "true" : "false",
    year: String(details.year)
  });

  if (timezone) {
    params.set("timezone", timezone);
  }

  return `/${target}?${params.toString()}` as Route;
}

function buildRetentionLinks(
  searchParams: HoroscopeSearchParams,
  selectedYear: number,
  selectedMonth: number
): FloatingMenuItem[] {
  return [
    { label: "오늘 브리핑", href: buildTodayPageHref(searchParams, getTodayInKorea()) },
    { label: "액션 캘린더", href: buildCalendarPageHref(searchParams, selectedYear, selectedMonth) },
    { label: "AI 코치", href: buildCoachPageHref(searchParams, selectedYear, selectedMonth) }
  ];
}

export function buildFloatingMenuItems({
  page,
  searchParams,
  hasCopyText = false,
  selectedYear = new Date().getFullYear(),
  selectedMonth = 1
}: FloatingMenuOptions): FloatingMenuItem[] {
  const safeSearchParams = searchParams ?? {};

  if (page === "home") {
    return [
      { label: "출생 정보 입력", href: "#birth-details" as Route },
      { label: "최근 차트", action: "recent" },
      { label: "맨 위로", action: "top" }
    ];
  }

  if (page === "chart") {
    return [
      ...(hasCopyText ? [{ label: "결과 복사", action: "copy" as const }] : []),
      { label: "월간 운세", href: buildHoroscopeHref(safeSearchParams, selectedYear) },
      { label: "입력 수정", href: "/#birth-details" as Route },
      { label: "맨 위로", action: "top" as const }
    ];
  }

  if (page === "retention") {
    return [
      { label: "출생 차트", href: buildChartPageHref(safeSearchParams) },
      { label: "월간 운세", href: buildHoroscopeHref(safeSearchParams, selectedYear, selectedMonth) },
      ...buildRetentionLinks(safeSearchParams, selectedYear, selectedMonth),
      { label: "입력 수정", href: "#birth-details" as Route },
      { label: "맨 위로", action: "top" as const }
    ];
  }

  const adjacent = getAdjacentHoroscopeMonths(selectedYear, selectedMonth);

  return [
    ...(hasCopyText ? [{ label: "결과 복사", action: "copy" as const }] : []),
    { label: "출생 차트", href: buildChartPageHref(safeSearchParams) },
    ...buildRetentionLinks(safeSearchParams, selectedYear, selectedMonth),
    { label: "이전 달", href: buildHoroscopeHref(safeSearchParams, adjacent.previous.year, adjacent.previous.month) },
    { label: "다음 달", href: buildHoroscopeHref(safeSearchParams, adjacent.next.year, adjacent.next.month) },
    { label: "입력 수정", href: "#birth-details" as Route },
    { label: "맨 위로", action: "top" as const }
  ];
}
