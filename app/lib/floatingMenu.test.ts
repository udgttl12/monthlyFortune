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
  city: "부산",
  country: "KR",
  timezone: "Asia/Seoul",
  timeUnknown: "false",
  year: "2026",
  month: "5"
};

test("chart floating menu puts copy first and links to horoscope with current birth details", () => {
  const items = buildFloatingMenuItems({
    page: "chart",
    searchParams: birthSearchParams,
    hasCopyText: true
  });

  assert.deepEqual(
    items.map((item) => item.label),
    ["ChatGPT용 전체 복사", "운세 보기", "입력 수정", "맨 위로"]
  );
  assert.equal(items[0].action, "copy");
  assert.equal(items[1].href?.startsWith("/horoscope?"), true);
  assert.match(items[1].href ?? "", /birthDate=1990-01-01/);
  assert.match(items[1].href ?? "", /country=KR/);
});

test("horoscope floating menu includes previous and next month links", () => {
  const items = buildFloatingMenuItems({
    page: "horoscope",
    searchParams: birthSearchParams,
    selectedYear: 2026,
    selectedMonth: 5,
    hasCopyText: true
  });

  assert.deepEqual(
    items.map((item) => item.label),
    ["ChatGPT용 전체 복사", "출생 차트 보기", "이전 달", "다음 달", "입력 수정", "맨 위로"]
  );
  assert.match(items[2].href ?? "", /month=4/);
  assert.match(items[3].href ?? "", /month=6/);
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
      city: "부산",
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
