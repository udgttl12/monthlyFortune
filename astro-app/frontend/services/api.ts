const BASE_URL = "http://localhost:8000";

export type BirthPayload = {
  name: string;
  birth_date: string;
  birth_time: string;
  latitude: string;
  longitude: string;
  timezone: string;
};

export async function fetchChart(payload: BirthPayload) {
  const params = new URLSearchParams(payload);
  const res = await fetch(`${BASE_URL}/api/chart?${params.toString()}`);
  if (!res.ok) {
    throw new Error("Failed to load chart");
  }
  return res.json();
}

export async function fetchMonthlyHoroscope(
  payload: BirthPayload,
  year: string,
  month: string,
) {
  const params = new URLSearchParams({ ...payload, year, month });
  const res = await fetch(`${BASE_URL}/api/horoscope/monthly?${params.toString()}`);
  if (!res.ok) {
    throw new Error("Failed to load monthly horoscope");
  }
  return res.json();
}
