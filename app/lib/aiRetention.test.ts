import assert from "node:assert/strict";
import test from "node:test";
import {
  buildAiRetentionApiParams,
  buildCalendarPageHref,
  buildCoachPageHref,
  buildTodayPageHref,
  getTodayInKorea
} from "./aiRetention";

const searchParams = {
  birthDate: "1990-01-01",
  birthTime: "09:00",
  city: "Seoul",
  country: "KR",
  year: "2026",
  month: "5",
  timeUnknown: "false"
};

test("buildAiRetentionApiParams maps country to countryCode", () => {
  const params = buildAiRetentionApiParams(searchParams, 2026, 5);

  assert.equal(params.get("countryCode"), "KR");
  assert.equal(params.get("month"), "5");
});

test("typed page hrefs preserve birth details", () => {
  assert.equal(buildTodayPageHref(searchParams, "2026-05-10").startsWith("/today?"), true);
  assert.equal(buildCalendarPageHref(searchParams, 2026, 5).startsWith("/calendar?"), true);
  assert.equal(buildCoachPageHref(searchParams, 2026, 5).startsWith("/coach?"), true);
});

test("getTodayInKorea returns yyyy-mm-dd", () => {
  assert.match(getTodayInKorea(new Date("2026-05-10T01:00:00Z")), /^\d{4}-\d{2}-\d{2}$/);
});
