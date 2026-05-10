import assert from "node:assert/strict";
import test from "node:test";
import { buildChartResultText, buildHoroscopeResultText } from "./resultText";
import type { NatalChartResponse } from "./resultText";
import type { MonthlyHoroscopeResponse, YearlyHoroscopeResponse } from "./horoscope";

const chartResult: NatalChartResponse = {
  points: [
    {
      name: "Sun",
      longitude: 10,
      sign: "Capricorn",
      degree: 10,
      minute: 5,
      retrograde: false,
      house: 1
    },
    {
      name: "Moon",
      longitude: 44,
      sign: "Taurus",
      degree: 14,
      minute: 20,
      retrograde: false,
      house: 5
    }
  ],
  angles: {
    asc: { longitude: 12, sign: "Aries", degree: 12, minute: 30 },
    mc: { longitude: 200, sign: "Capricorn", degree: 20, minute: 0 }
  },
  houses: [{ houseNumber: 1, sign: "Aries", cuspLongitude: 0 }],
  aspects: [
    {
      pointA: "Sun",
      pointB: "Moon",
      aspect: "Trine",
      orb: 1.234,
      applying: true
    }
  ],
  location: {
    resolvedName: "Busan, South Korea",
    latitude: 35.1796,
    longitude: 129.0756,
    timezone: "Asia/Seoul",
    countryCode: "KR"
  }
};

const yearly: YearlyHoroscopeResponse = {
  year: 2026,
  profileSummary: "연간 흐름 요약",
  months: [
    {
      month: 5,
      title: "집중의 달",
      focusAreas: ["커리어", "관계"],
      intensityScore: 8,
      topTheme: "방향 정리",
      luckyWindow: {
        startDate: "2026-05-10",
        endDate: "2026-05-12",
        label: "5월 10일-12일"
      },
      cautionWindow: {
        startDate: "2026-05-20",
        endDate: "2026-05-22",
        label: "5월 20일-22일"
      }
    }
  ]
};

const monthly: MonthlyHoroscopeResponse = {
  year: 2026,
  month: 5,
  summary: "월간 요약",
  sections: {
    career: "커리어 내용",
    money: "재정 내용",
    love: "관계 내용",
    risk: "리스크 내용"
  },
  luckyDates: [{ date: "2026-05-11", label: "좋은 날", reason: "흐름이 부드럽습니다." }],
  cautionDates: [{ date: "2026-05-21", label: "주의 날", reason: "과속을 피하세요." }],
  evidence: [
    {
      date: "2026-05-11",
      headline: "태양 흐름",
      detail: "핵심 포인트와 조화를 이룹니다.",
      tone: "supportive"
    }
  ],
  llmEnhanced: true
};

test("buildChartResultText includes the full chart sections for ChatGPT", () => {
  const text = buildChartResultText({
    searchParams: {
      birthDate: "1990-01-01",
      birthTime: "09:30",
      city: "부산",
      country: "KR",
      timezone: "Asia/Seoul"
    },
    data: chartResult
  });

  assert.match(text, /# 출생 차트 결과/);
  assert.match(text, /생년월일: 1990\.01\.01/);
  assert.match(text, /태양: Capricorn 10°05′ · 1H/);
  assert.match(text, /홀사인 하우스/);
  assert.match(text, /태양 Trine 달: Orb 1\.23°/);
});

test("buildHoroscopeResultText includes yearly and monthly result content", () => {
  const text = buildHoroscopeResultText({
    searchParams: {
      birthDate: "1990-01-01",
      birthTime: "09:30",
      city: "부산",
      country: "KR",
      timezone: "Asia/Seoul"
    },
    yearly,
    monthly,
    selectedMonth: 5
  });

  assert.match(text, /# 개인 맞춤 운세 결과/);
  assert.match(text, /2026년 연간 개요/);
  assert.match(text, /### 5월 - 집중의 달/);
  assert.match(text, /리딩 유형: AI 확장 리딩/);
  assert.match(text, /좋은 날짜/);
  assert.match(text, /5월 11일 - 좋은 날/);
});
