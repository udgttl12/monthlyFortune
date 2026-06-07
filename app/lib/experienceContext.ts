import type { Route } from "next";
import type { LastViewedBirthDetails } from "@/app/lib/birthDetailsStorage";
import { buildCoachPageHref, buildTodayPageHref, getTodayInKorea } from "@/app/lib/aiRetention";
import { buildHoroscopePageHref, type HoroscopeSearchParams } from "@/app/lib/horoscope";
import { parseBirthDateInput } from "@/app/lib/birthDateInput";
import { parseBirthTimeInput } from "@/app/lib/birthTimeInput";
import { getDefaultTimezone, getLocationOption } from "@/app/lib/locations";

export type MonthlyResumeLinkKind = "horoscope" | "today" | "coach" | "chart";

export type MonthlyResumeLink = {
  readonly kind: MonthlyResumeLinkKind;
  readonly label: string;
  readonly description: string;
  readonly href: Route;
};

type YearMonth = {
  readonly year: number;
  readonly month: number;
};

function getKoreanYearMonth(referenceDate: Date): YearMonth {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "numeric"
  }).formatToParts(referenceDate);
  const year = Number(parts.find((part) => part.type === "year")?.value);
  const month = Number(parts.find((part) => part.type === "month")?.value);

  return {
    year: Number.isInteger(year) ? year : referenceDate.getFullYear(),
    month: Number.isInteger(month) ? month : referenceDate.getMonth() + 1
  };
}

export function buildSearchParamsFromBirthDetails(
  details: LastViewedBirthDetails,
  referenceDate: Date = new Date()
): HoroscopeSearchParams {
  const { year, month } = getKoreanYearMonth(referenceDate);
  const birthDate = parseBirthDateInput(details.birthDateInput) ?? "";
  const parsedBirthTime = parseBirthTimeInput(details.birthTimeInput);
  const location = getLocationOption(details.city, details.country);
  const timezone = location?.timezone ?? getDefaultTimezone(details.country);

  return {
    birthDate,
    birthTime: details.timeUnknown ? "12:00" : parsedBirthTime ?? "",
    city: details.city,
    country: details.country,
    timezone,
    year: String(year),
    month: String(month),
    timeUnknown: details.timeUnknown ? "true" : "false"
  };
}

function buildChartPageHref(searchParams: HoroscopeSearchParams): Route {
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

export function formatBirthProfileSummary(details: LastViewedBirthDetails): string {
  const birthDate = parseBirthDateInput(details.birthDateInput) ?? "생년월일 미입력";
  const parsedBirthTime = parseBirthTimeInput(details.birthTimeInput);
  const timeLabel = details.timeUnknown ? "출생 시간 미상" : parsedBirthTime ?? "출생 시간 미입력";

  return `${birthDate} · ${timeLabel} · ${details.city}`;
}

export function buildMonthlyResumeLinks(
  details: LastViewedBirthDetails,
  referenceDate: Date = new Date()
): readonly MonthlyResumeLink[] {
  const searchParams = buildSearchParamsFromBirthDetails(details, referenceDate);
  const selectedYear = Number(searchParams.year);
  const selectedMonth = Number(searchParams.month);

  return [
    {
      kind: "horoscope",
      label: "이번 달 월운",
      description: "용용이가 이번 달 흐름을 먼저 정리해줘요.",
      href: buildHoroscopePageHref(searchParams, selectedYear, selectedMonth)
    },
    {
      kind: "today",
      label: "오늘 브리핑",
      description: "월운을 오늘 할 일로 작게 쪼갭니다.",
      href: buildTodayPageHref(searchParams, getTodayInKorea(referenceDate))
    },
    {
      kind: "coach",
      label: "AI 코치",
      description: "이번 달 고민을 월운 맥락으로 물어봅니다.",
      href: buildCoachPageHref(searchParams, selectedYear, selectedMonth)
    },
    {
      kind: "chart",
      label: "출생 차트",
      description: "월운 해석에 쓰인 기본 근거를 확인합니다.",
      href: buildChartPageHref(searchParams)
    }
  ];
}
