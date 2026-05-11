import type { Route } from "next";
import type { HoroscopeSearchParams } from "@/app/lib/horoscope";

const API_BASE_URL = process.env.MONTHLY_FORTUNE_API_URL ?? "http://127.0.0.1:8000";

export interface AiRetentionSearchParams extends HoroscopeSearchParams {
  targetDate?: string;
}

export interface ActionCalendarDay {
  date: string;
  score: number;
  tone: "supportive" | "neutral" | "challenging";
  title: string;
  action: string;
  avoid: string;
  reason: string;
  categories: string[];
}

export interface ActionCalendarResponse {
  year: number;
  month: number;
  profileSummary: string;
  llmEnhanced: boolean;
  days: ActionCalendarDay[];
}

export interface DailyBriefResponse {
  date: string;
  score: number;
  tone: "supportive" | "neutral" | "challenging";
  headline: string;
  summary: string;
  bestTimeHint: string;
  avoidTimeHint: string;
  action: string;
  avoid: string;
  reflectionPrompt: string;
  llmEnhanced: boolean;
}

export interface CoachResponse {
  question: string;
  answer: string;
  recommendedDates: Array<{ date: string; label: string; reason: string }>;
  cautionDates: Array<{ date: string; label: string; reason: string }>;
  firstAction: string;
  messageDraft: string;
  reasoningSummary: string;
  disclaimer: string;
  llmEnhanced: boolean;
}

export function buildAiRetentionApiParams(
  searchParams: HoroscopeSearchParams,
  selectedYear: number,
  selectedMonth: number
): URLSearchParams {
  const params = new URLSearchParams({
    birthDate: searchParams.birthDate ?? "",
    birthTime: searchParams.birthTime ?? "",
    city: searchParams.city ?? "",
    countryCode: searchParams.country ?? "",
    year: String(selectedYear),
    month: String(selectedMonth)
  });

  if (searchParams.timezone) {
    params.set("timezone", searchParams.timezone);
  }

  return params;
}

export function getTodayInKorea(referenceDate: Date = new Date()): string {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(referenceDate);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

export function buildTodayPageHref(searchParams: HoroscopeSearchParams, targetDate: string): Route {
  const params = buildPageParams(searchParams);
  params.set("targetDate", targetDate);
  return `/today?${params.toString()}` as Route;
}

export function buildCalendarPageHref(
  searchParams: HoroscopeSearchParams,
  selectedYear: number,
  selectedMonth: number
): Route {
  const params = buildPageParams(searchParams);
  params.set("year", String(selectedYear));
  params.set("month", String(selectedMonth));
  return `/calendar?${params.toString()}` as Route;
}

export function buildCoachPageHref(
  searchParams: HoroscopeSearchParams,
  selectedYear: number,
  selectedMonth: number
): Route {
  const params = buildPageParams(searchParams);
  params.set("year", String(selectedYear));
  params.set("month", String(selectedMonth));
  return `/coach?${params.toString()}` as Route;
}

export async function fetchActionCalendar(
  searchParams: HoroscopeSearchParams,
  year: number,
  month: number
): Promise<ActionCalendarResponse | null> {
  try {
    const params = buildAiRetentionApiParams(searchParams, year, month);
    const response = await fetch(`${API_BASE_URL}/api/ai-retention/action-calendar?${params.toString()}`, {
      cache: "no-store"
    });
    return response.ok ? response.json() : null;
  } catch {
    return null;
  }
}

export async function fetchDailyBrief(
  searchParams: HoroscopeSearchParams,
  year: number,
  month: number,
  targetDate: string
): Promise<DailyBriefResponse | null> {
  try {
    const params = buildAiRetentionApiParams(searchParams, year, month);
    params.set("targetDate", targetDate);
    const response = await fetch(`${API_BASE_URL}/api/ai-retention/daily-brief?${params.toString()}`, {
      cache: "no-store"
    });
    return response.ok ? response.json() : null;
  } catch {
    return null;
  }
}

function buildPageParams(searchParams: HoroscopeSearchParams): URLSearchParams {
  const params = new URLSearchParams({
    birthDate: searchParams.birthDate ?? "",
    birthTime: searchParams.birthTime ?? "",
    city: searchParams.city ?? "",
    country: searchParams.country ?? "",
    year: searchParams.year ?? String(new Date().getFullYear()),
    month: searchParams.month ?? String(new Date().getMonth() + 1),
    timeUnknown: searchParams.timeUnknown ?? "false"
  });

  if (searchParams.timezone) {
    params.set("timezone", searchParams.timezone);
  }

  return params;
}
