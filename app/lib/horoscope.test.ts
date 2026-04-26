import assert from "node:assert/strict";
import test from "node:test";
import {
  buildHoroscopeApiParams,
  buildHoroscopePageHref,
  getSelectedHoroscopeMonth,
  getSelectedHoroscopeYear,
  hasRequiredBirthDetails
} from "./horoscope";

test("hasRequiredBirthDetails returns false when required params are missing", () => {
  assert.equal(hasRequiredBirthDetails({ birthDate: "1988-12-06", city: "Busan" }), false);
});

test("selected year defaults to the current year when query is missing", () => {
  const referenceDate = new Date("2026-04-26T12:00:00");
  assert.equal(getSelectedHoroscopeYear({}, referenceDate), 2026);
});

test("selected month defaults to the current month for the current year", () => {
  const referenceDate = new Date("2026-04-26T12:00:00");
  assert.equal(getSelectedHoroscopeMonth(2026, undefined, referenceDate), 4);
});

test("selected month defaults to january for a non-current year", () => {
  const referenceDate = new Date("2026-04-26T12:00:00");
  assert.equal(getSelectedHoroscopeMonth(2025, undefined, referenceDate), 1);
});

test("query builders preserve birth params and selected month", () => {
  const searchParams = {
    birthDate: "1988-12-06",
    birthTime: "19:59",
    city: "Busan",
    country: "KR",
    timezone: "Asia/Seoul",
    timeUnknown: "false"
  };

  const apiParams = buildHoroscopeApiParams(searchParams, 2026, 4);
  const pageHref = buildHoroscopePageHref(searchParams, 2026, 4);

  assert.equal(apiParams.get("countryCode"), "KR");
  assert.equal(apiParams.get("month"), "4");
  assert.match(pageHref, /month=4/);
  assert.match(pageHref, /country=KR/);
});
