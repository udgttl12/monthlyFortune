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

export type FloatingMenuPage = "home" | "chart" | "horoscope";
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

export function buildFloatingMenuItems({
  page,
  searchParams,
  hasCopyText = false,
  selectedYear = new Date().getFullYear(),
  selectedMonth = 1
}: FloatingMenuOptions): FloatingMenuItem[] {
  if (page === "home") {
    return [
      { label: "출생 차트 입력", href: "#birth-details" as Route },
      { label: "최근 결과", action: "recent" },
      { label: "맨 위로", action: "top" }
    ];
  }

  if (page === "chart") {
    return [
      ...(hasCopyText ? [{ label: "결과 복사", action: "copy" as const }] : []),
      { label: "월간 운세", href: buildHoroscopeHref(searchParams, selectedYear) },
      { label: "입력 수정", href: "/#birth-details" as Route },
      { label: "맨 위로", action: "top" as const }
    ];
  }

  const adjacent = getAdjacentHoroscopeMonths(selectedYear, selectedMonth);
  const safeSearchParams = searchParams ?? {};

  return [
    ...(hasCopyText ? [{ label: "결과 복사", action: "copy" as const }] : []),
    { label: "출생 차트", href: buildChartPageHref(safeSearchParams) },
    { label: "오늘 브리핑", href: buildTodayPageHref(safeSearchParams, getTodayInKorea()) },
    { label: "액션 캘린더", href: buildCalendarPageHref(safeSearchParams, selectedYear, selectedMonth) },
    { label: "AI 코치", href: buildCoachPageHref(safeSearchParams, selectedYear, selectedMonth) },
    { label: "이전 달", href: buildHoroscopeHref(safeSearchParams, adjacent.previous.year, adjacent.previous.month) },
    { label: "다음 달", href: buildHoroscopeHref(safeSearchParams, adjacent.next.year, adjacent.next.month) },
    { label: "입력 수정", href: "#birth-details" as Route },
    { label: "맨 위로", action: "top" as const }
  ];
}
