import assert from "node:assert/strict";
import test from "node:test";
import {
  buildFloatingMenuItems,
  buildStoredBirthDetailsHref,
  getAdjacentHoroscopeMonths
} from "./floatingMenu";

const birthSearchParams = {
  birthDate: "1990-01-01",
  birthTime: "09:30",
  city: "Seoul",
  country: "KR",
  timezone: "Asia/Seoul",
  timeUnknown: "false",
  year: "2026",
  month: "5"
};

test("chart floating menu puts copy first and links to horoscope with readable labels", () => {
  const items = buildFloatingMenuItems({
    page: "chart",
    searchParams: birthSearchParams,
    hasCopyText: true
  });

  assert.deepEqual(
    items.map((item) => item.label),
    ["결과 복사", "월간 운세", "입력 수정", "맨 위로"]
  );
  assert.equal(items[0].action, "copy");
  assert.equal(items[1].href?.startsWith("/horoscope?"), true);
  assert.match(items[1].href ?? "", /birthDate=1990-01-01/);
  assert.match(items[1].href ?? "", /country=KR/);
});

test("horoscope floating menu uses readable Korean labels and includes retention links", () => {
  const items = buildFloatingMenuItems({
    page: "horoscope",
    searchParams: birthSearchParams,
    selectedYear: 2026,
    selectedMonth: 5,
    hasCopyText: true
  });

  assert.deepEqual(
    items.map((item) => item.label),
    ["결과 복사", "출생 차트", "오늘 브리핑", "액션 캘린더", "AI 코치", "이전 달", "다음 달", "입력 수정", "맨 위로"]
  );
  assert.equal(items.some((item) => item.href?.startsWith("/today?")), true);
  assert.equal(items.some((item) => item.href?.startsWith("/calendar?")), true);
  assert.equal(items.some((item) => item.href?.startsWith("/coach?")), true);
  assert.equal(items.some((item) => item.href?.match(/month=4/)), true);
  assert.equal(items.some((item) => item.href?.match(/month=6/)), true);
});

test("retention pages keep the main navigation visible", () => {
  const items = buildFloatingMenuItems({
    page: "retention",
    searchParams: birthSearchParams,
    selectedYear: 2026,
    selectedMonth: 5
  });

  assert.deepEqual(
    items.map((item) => item.label),
    ["출생 차트", "월간 운세", "오늘 브리핑", "액션 캘린더", "AI 코치", "입력 수정", "맨 위로"]
  );
  assert.equal(items.some((item) => item.href?.startsWith("/horoscope?")), true);
  assert.equal(items.some((item) => item.href?.startsWith("/calendar?")), true);
});

test("adjacent horoscope months cross year boundaries", () => {
  assert.deepEqual(getAdjacentHoroscopeMonths(2026, 1), {
    previous: { year: 2025, month: 12 },
    next: { year: 2026, month: 2 }
  });

  assert.deepEqual(getAdjacentHoroscopeMonths(2026, 12), {
    previous: { year: 2026, month: 11 },
    next: { year: 2027, month: 1 }
  });
});

test("stored birth details can rebuild a chart href", () => {
  const href = buildStoredBirthDetailsHref(
    {
      birthDateInput: "19900101",
      birthTimeInput: "0930",
      city: "Seoul",
      country: "KR",
      timeUnknown: false,
      year: 2026
    },
    "chart"
  );

  assert.match(href, /^\/chart\?/);
  assert.match(href, /birthDate=1990-01-01/);
  assert.match(href, /birthTime=09%3A30/);
  assert.match(href, /timezone=Asia%2FSeoul/);
});
