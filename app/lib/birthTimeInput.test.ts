import assert from "node:assert/strict";
import test from "node:test";
import { normalizeBirthTimeInput, parseBirthTimeInput } from "./birthTimeInput";

test("normalizeBirthTimeInput keeps only the first four digits", () => {
  assert.equal(normalizeBirthTimeInput("09:30abc"), "0930");
  assert.equal(normalizeBirthTimeInput("235912"), "2359");
});

test("parseBirthTimeInput converts hhmm to HH:MM", () => {
  assert.equal(parseBirthTimeInput("0930"), "09:30");
  assert.equal(parseBirthTimeInput("2359"), "23:59");
});

test("parseBirthTimeInput rejects incomplete or impossible times", () => {
  assert.equal(parseBirthTimeInput("930"), null);
  assert.equal(parseBirthTimeInput("2460"), null);
  assert.equal(parseBirthTimeInput("2400"), null);
});
