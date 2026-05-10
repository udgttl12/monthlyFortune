import { normalizeBirthDateInput } from "./birthDateInput";
import { normalizeBirthTimeInput } from "./birthTimeInput";

export const LAST_VIEWED_BIRTH_DETAILS_STORAGE_KEY = "monthlyFortune.lastViewedBirthDetails.v1";

export interface LastViewedBirthDetails {
  birthDateInput: string;
  birthTimeInput: string;
  city: string;
  country: string;
  timeUnknown: boolean;
  year: number;
}

interface BirthDetailsStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function readLastViewedBirthDetails(storage: BirthDetailsStorage): LastViewedBirthDetails | null {
  try {
    const rawValue = storage.getItem(LAST_VIEWED_BIRTH_DETAILS_STORAGE_KEY);

    if (!rawValue) {
      return null;
    }

    const parsed: unknown = JSON.parse(rawValue);

    if (!isRecord(parsed)) {
      return null;
    }

    return {
      birthDateInput:
        typeof parsed.birthDateInput === "string" ? normalizeBirthDateInput(parsed.birthDateInput) : "",
      birthTimeInput:
        typeof parsed.birthTimeInput === "string" ? normalizeBirthTimeInput(parsed.birthTimeInput) : "1200",
      city: typeof parsed.city === "string" ? parsed.city : "서울",
      country: typeof parsed.country === "string" ? parsed.country : "KR",
      timeUnknown: typeof parsed.timeUnknown === "boolean" ? parsed.timeUnknown : false,
      year: typeof parsed.year === "number" && Number.isInteger(parsed.year) ? parsed.year : new Date().getFullYear()
    };
  } catch {
    return null;
  }
}

export function writeLastViewedBirthDetails(
  storage: BirthDetailsStorage,
  details: LastViewedBirthDetails
): void {
  try {
    storage.setItem(
      LAST_VIEWED_BIRTH_DETAILS_STORAGE_KEY,
      JSON.stringify({
        birthDateInput: normalizeBirthDateInput(details.birthDateInput),
        birthTimeInput: normalizeBirthTimeInput(details.birthTimeInput),
        city: details.city,
        country: details.country,
        timeUnknown: details.timeUnknown,
        year: details.year
      })
    );
  } catch {
    // Persisting the last viewed chart settings should never block the chart request.
  }
}
