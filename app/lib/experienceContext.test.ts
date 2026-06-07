import assert from "node:assert/strict";
import test from "node:test";
import { buildMonthlyResumeLinks, buildSearchParamsFromBirthDetails } from "./experienceContext";

const storedDetails = {
  birthDateInput: "1988-12-06",
  birthTimeInput: "19:59",
  city: "Busan",
  country: "KR",
  timeUnknown: false,
  year: 2025
};

test("buildSearchParamsFromBirthDetails sanitizes stored profile for monthly links", () => {
  const searchParams = buildSearchParamsFromBirthDetails(storedDetails, new Date("2026-04-10T00:00:00+09:00"));

  assert.deepEqual(searchParams, {
    birthDate: "1988-12-06",
    birthTime: "19:59",
    city: "Busan",
    country: "KR",
    timezone: "Asia/Seoul",
    year: "2026",
    month: "4",
    timeUnknown: "false"
  });
});

test("buildMonthlyResumeLinks prioritizes 월운 then today then coach then chart", () => {
  const links = buildMonthlyResumeLinks(storedDetails, new Date("2026-04-10T00:00:00+09:00"));

  assert.deepEqual(
    links.map((link) => link.kind),
    ["horoscope", "today", "coach", "chart"]
  );
  assert.equal(links[0]?.label, "이번 달 월운");
  assert.equal(links[0]?.href.startsWith("/horoscope?"), true);
  assert.equal(links[1]?.href.includes("/today?"), true);
  assert.equal(links[2]?.href.includes("/coach?"), true);
  assert.equal(links[3]?.href.includes("/chart?"), true);
});
