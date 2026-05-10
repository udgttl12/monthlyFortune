import assert from "node:assert/strict";
import test from "node:test";
import {
  LAST_VIEWED_BIRTH_DETAILS_STORAGE_KEY,
  readLastViewedBirthDetails,
  writeLastViewedBirthDetails
} from "./birthDetailsStorage";

class MemoryStorage {
  private values = new Map<string, string>();

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }
}

test("writeLastViewedBirthDetails stores the submitted chart settings", () => {
  const storage = new MemoryStorage();

  writeLastViewedBirthDetails(storage, {
    birthDateInput: "19881206",
    birthTimeInput: "0930",
    city: "서울",
    country: "KR",
    timeUnknown: false,
    year: 2026
  });

  assert.deepEqual(JSON.parse(storage.getItem(LAST_VIEWED_BIRTH_DETAILS_STORAGE_KEY) ?? "{}"), {
    birthDateInput: "19881206",
    birthTimeInput: "0930",
    city: "서울",
    country: "KR",
    timeUnknown: false,
    year: 2026
  });
});

test("readLastViewedBirthDetails normalizes stored date and time digits", () => {
  const storage = new MemoryStorage();
  storage.setItem(
    LAST_VIEWED_BIRTH_DETAILS_STORAGE_KEY,
    JSON.stringify({
      birthDateInput: "1988-12-06",
      birthTimeInput: "09:30",
      city: "서울",
      country: "KR",
      timeUnknown: false,
      year: 2026
    })
  );

  assert.deepEqual(readLastViewedBirthDetails(storage), {
    birthDateInput: "19881206",
    birthTimeInput: "0930",
    city: "서울",
    country: "KR",
    timeUnknown: false,
    year: 2026
  });
});

test("readLastViewedBirthDetails returns null for missing or malformed storage", () => {
  assert.equal(readLastViewedBirthDetails(new MemoryStorage()), null);

  const storage = new MemoryStorage();
  storage.setItem(LAST_VIEWED_BIRTH_DETAILS_STORAGE_KEY, "{");

  assert.equal(readLastViewedBirthDetails(storage), null);
});
