import assert from "node:assert/strict";
import test from "node:test";
import { normalizeBirthDateInput, parseBirthDateInput } from "./birthDateInput";

test("normalizeBirthDateInput keeps only the first eight digits", () => {
  assert.equal(normalizeBirthDateInput("1988-12-06abc"), "19881206");
  assert.equal(normalizeBirthDateInput("198812061234"), "19881206");
});

test("parseBirthDateInput converts yyyymmdd to an ISO date", () => {
  assert.equal(parseBirthDateInput("19881206"), "1988-12-06");
});

test("parseBirthDateInput rejects incomplete or impossible dates", () => {
  assert.equal(parseBirthDateInput("198812"), null);
  assert.equal(parseBirthDateInput("20250230"), null);
});

test("parseBirthDateInput accepts valid leap days", () => {
  assert.equal(parseBirthDateInput("20000229"), "2000-02-29");
});
