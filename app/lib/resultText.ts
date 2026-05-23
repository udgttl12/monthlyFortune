import { getCountryLabel, getDefaultTimezone } from "@/app/lib/locations";
import {
  HoroscopeSearchParams,
  MonthlyHoroscopeResponse,
  YearlyHoroscopeResponse,
  formatHoroscopeDate
} from "@/app/lib/horoscope";

export interface ChartPoint {
  name: string;
  longitude: number;
  sign: string;
  degree: number;
  minute: number;
  retrograde: boolean;
  house: number | null;
}

export interface ChartAngle {
  longitude: number;
  sign: string;
  degree: number;
  minute: number;
}

export interface ChartHouse {
  houseNumber: number;
  sign: string;
  cuspLongitude: number;
}

export interface ChartAspect {
  pointA: string;
  pointB: string;
  aspect: string;
  orb: number;
  applying: boolean;
}

export interface NatalChartResponse {
  points: ChartPoint[];
  angles: {
    asc: ChartAngle;
    mc: ChartAngle;
  };
  houses: ChartHouse[];
  aspects: ChartAspect[];
  location: {
    resolvedName: string;
    latitude: number;
    longitude: number;
    timezone: string;
    countryCode: string;
  };
}

export const CORE_POINT_ORDER = ["Sun", "Moon", "Mercury", "Venus", "Mars"];

export const POINT_LABELS: Record<string, string> = {
  Sun: "태양",
  Moon: "달",
  Mercury: "수성",
  Venus: "금성",
  Mars: "화성",
  Jupiter: "목성",
  Saturn: "토성",
  Uranus: "천왕성",
  Neptune: "해왕성",
  Pluto: "명왕성",
  "North Node": "북노드",
  Lilith: "릴리스",
  Chiron: "키론",
  Fortune: "포춘",
  Vertex: "버텍스",
  ASC: "ASC",
  MC: "MC",
  DSC: "DSC",
  IC: "IC"
};

interface ChartResultTextOptions {
  searchParams: {
    birthDate?: string;
    birthTime?: string;
    city?: string;
    country?: string;
    timezone?: string;
    timeUnknown?: string;
  };
  data: NatalChartResponse;
}

interface HoroscopeResultTextOptions {
  searchParams: HoroscopeSearchParams;
  yearly: YearlyHoroscopeResponse;
  monthly: MonthlyHoroscopeResponse;
  selectedMonth: number;
}

export function formatBirthDate(value?: string) {
  if (!value) {
    return "입력하지 않음";
  }

  return value.replaceAll("-", ".");
}

export function formatBirthTime(value?: string, timeUnknown?: string) {
  if (!value) {
    return "입력하지 않음";
  }

  if (timeUnknown === "true") {
    return `${value} (정오 기준 임시값)`;
  }

  return value;
}

export function formatDegree(sign: string, degree: number, minute: number) {
  return `${sign} ${String(degree).padStart(2, "0")}°${String(minute).padStart(2, "0")}′`;
}

export function formatAspectDirection(applying: boolean) {
  return applying ? "정확각으로 접근 중" : "정확각을 지난 상태";
}

function formatPoint(point: ChartPoint) {
  return [
    `${POINT_LABELS[point.name] ?? point.name}: ${formatDegree(point.sign, point.degree, point.minute)}`,
    point.house ? `${point.house}H` : "",
    point.retrograde ? "역행" : ""
  ]
    .filter(Boolean)
    .join(" · ");
}

function formatAspect(aspect: ChartAspect) {
  const pointA = POINT_LABELS[aspect.pointA] ?? aspect.pointA;
  const pointB = POINT_LABELS[aspect.pointB] ?? aspect.pointB;
  return `${pointA} ${aspect.aspect} ${pointB}: Orb ${aspect.orb.toFixed(2)}° · ${formatAspectDirection(
    aspect.applying
  )}`;
}

function section(title: string, lines: string[]) {
  const content = lines.filter(Boolean);

  if (content.length === 0) {
    return "";
  }

  return [`## ${title}`, ...content].join("\n");
}

function bulletList(lines: string[]) {
  return lines.map((line) => `- ${line}`);
}

export function buildChartResultText({ searchParams, data }: ChartResultTextOptions) {
  const countryLabel = getCountryLabel(searchParams.country);
  const fallbackTimezone = searchParams.timezone ?? getDefaultTimezone(searchParams.country);
  const primaryPoints = data.points.filter((point) => CORE_POINT_ORDER.includes(point.name));

  return [
    "# 출생 차트 결과",
    section("입력 정보", [
      `생년월일: ${formatBirthDate(searchParams.birthDate)}`,
      `출생 시간: ${formatBirthTime(searchParams.birthTime, searchParams.timeUnknown)}`,
      `국가: ${countryLabel}`,
      `입력 도시: ${searchParams.city ?? "입력하지 않음"}`,
      `입력 timezone: ${fallbackTimezone}`
    ]),
    section("확정된 위치", [
      `위치: ${data.location.resolvedName}`,
      `timezone: ${data.location.timezone}`,
      `좌표: ${data.location.latitude.toFixed(4)}, ${data.location.longitude.toFixed(4)}`
    ]),
    section("핵심 각도", [
      `ASC: ${formatDegree(data.angles.asc.sign, data.angles.asc.degree, data.angles.asc.minute)}`,
      `MC: ${formatDegree(data.angles.mc.sign, data.angles.mc.degree, data.angles.mc.minute)}`
    ]),
    section("핵심 행성 요약", bulletList(primaryPoints.map(formatPoint))),
    section("전체 행성과 포인트", bulletList(data.points.map(formatPoint))),
    section(
      "홀사인 하우스",
      bulletList(data.houses.map((house) => `${house.houseNumber}하우스: ${house.sign} 0°00′`))
    ),
    section("어스펙트 전체", bulletList(data.aspects.map(formatAspect)))
  ]
    .filter(Boolean)
    .join("\n\n");
}

export function buildHoroscopeResultText({
  searchParams,
  yearly,
  monthly,
  selectedMonth
}: HoroscopeResultTextOptions) {
  const countryLabel = getCountryLabel(searchParams.country);
  const fallbackTimezone = searchParams.timezone ?? getDefaultTimezone(searchParams.country);

  return [
    "# 개인 맞춤 운세 결과",
    section("입력 정보", [
      `생년월일: ${formatBirthDate(searchParams.birthDate)}`,
      `출생 시간: ${formatBirthTime(searchParams.birthTime, searchParams.timeUnknown)}`,
      `국가: ${countryLabel}`,
      `입력 도시: ${searchParams.city ?? "입력하지 않음"}`,
      `입력 timezone: ${fallbackTimezone}`,
      `조회 연도: ${yearly.year}`,
      `선택 월: ${selectedMonth}월`
    ]),
    section(`${yearly.year}년 연간 개요`, [
      yearly.profileSummary,
      ...yearly.months.flatMap((item) => [
        `### ${item.month}월 - ${item.title}`,
        `강도: ${item.intensityScore}/10`,
        `핵심 테마: ${item.topTheme}`,
        `집중 영역: ${item.focusAreas.join(", ")}`,
        `좋은 구간: ${item.luckyWindow.label}`,
        `주의 구간: ${item.cautionWindow.label}`
      ])
    ]),
    section(`${monthly.year}년 ${monthly.month}월 상세 리딩`, [
      `리딩 유형: ${monthly.llmEnhanced ? "AI 확장 리딩" : "기본 계산 리딩"}`,
      `요약: ${monthly.summary}`,
      `커리어: ${monthly.sections.career}`,
      `재정: ${monthly.sections.money}`,
      `관계: ${monthly.sections.love}`,
      `컨디션: ${monthly.sections.risk}`
    ]),
    section(
      "좋은 날짜",
      bulletList(monthly.luckyDates.map((item) => `${formatHoroscopeDate(item.date)} - ${item.label}: ${item.reason}`))
    ),
    section(
      "주의 날짜",
      bulletList(
        monthly.cautionDates.map((item) => `${formatHoroscopeDate(item.date)} - ${item.label}: ${item.reason}`)
      )
    ),
    section(
      "해석 근거",
      bulletList(monthly.evidence.map((item) => `${formatHoroscopeDate(item.date)} - ${item.headline}: ${item.detail}`))
    )
  ]
    .filter(Boolean)
    .join("\n\n");
}
