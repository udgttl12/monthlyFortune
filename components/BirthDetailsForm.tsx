"use client";

import { ChangeEvent, useState } from "react";
import {
  COUNTRY_OPTIONS,
  getCitiesByCountry,
  getDefaultTimezone,
  getLocationOption
} from "@/app/lib/locations";

const TIME_PRESETS = [
  { label: "이른 아침 06:00", value: "06:00" },
  { label: "정오 12:00", value: "12:00" },
  { label: "오후 15:00", value: "15:00" },
  { label: "저녁 18:00", value: "18:00" }
];

interface BirthDetailsFormProps {
  action?: string;
  submitLabel?: string;
  secondarySubmitAction?: string;
  secondarySubmitLabel?: string;
  showYearField?: boolean;
  defaultYear?: number;
}

export default function BirthDetailsForm({
  action = "/chart",
  submitLabel = "출생 차트 보기",
  secondarySubmitAction,
  secondarySubmitLabel,
  showYearField = false,
  defaultYear = new Date().getFullYear()
}: BirthDetailsFormProps) {
  const [country, setCountry] = useState("KR");
  const [city, setCity] = useState("서울");
  const [birthTime, setBirthTime] = useState("12:00");
  const [timeUnknown, setTimeUnknown] = useState(false);
  const [year, setYear] = useState(defaultYear);

  const cityOptions = getCitiesByCountry(country);
  const matchedLocation = getLocationOption(city, country);
  const timezone = matchedLocation?.timezone ?? getDefaultTimezone(country);
  const isKnownCity = matchedLocation !== undefined;

  function handleCountryChange(event: ChangeEvent<HTMLSelectElement>) {
    const nextCountry = event.target.value;
    const nextCity = getCitiesByCountry(nextCountry)[0]?.city ?? "";

    setCountry(nextCountry);
    setCity(nextCity);
  }

  return (
    <form className="form-grid" action={action} method="GET">
      <div className="field-card full-width">
        <h3>1. 생년월일</h3>
        <p className="helper-text">
          입력한 날짜와 시간은 선택한 도시의 표준시 기준으로 해석한 뒤 차트와 운세 계산에 사용합니다.
        </p>
        <div className="field-grid">
          <label>
            생년월일
            <input type="date" name="birthDate" required />
          </label>

          {showYearField ? (
            <label>
              조회 연도
              <input
                type="number"
                name="year"
                min={1900}
                max={2100}
                value={year}
                onChange={(event) => setYear(Number(event.target.value))}
                required
              />
            </label>
          ) : (
            <input type="hidden" name="year" value={year} />
          )}
        </div>
      </div>

      <div className="field-card">
        <h3>2. 출생 시간</h3>
        <p className="helper-text">
          시간을 모르면 정오 12:00 기준으로 계산합니다. 이 경우 ASC와 하우스, 날짜 단위 운세는 참고용으로
          보는 편이 좋습니다.
        </p>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={timeUnknown}
            onChange={(event) => {
              const checked = event.target.checked;

              setTimeUnknown(checked);
              if (checked) {
                setBirthTime("12:00");
              }
            }}
          />
          출생 시간을 정확히 모름
        </label>

        {timeUnknown ? <input type="hidden" name="birthTime" value="12:00" /> : null}
        <input type="hidden" name="timeUnknown" value={timeUnknown ? "true" : "false"} />

        <label>
          출생 시간
          <input
            type="time"
            name={timeUnknown ? undefined : "birthTime"}
            value={birthTime}
            onChange={(event) => setBirthTime(event.target.value)}
            disabled={timeUnknown}
            required={!timeUnknown}
          />
        </label>

        <div className="preset-row">
          {TIME_PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              className="preset-chip"
              onClick={() => {
                setBirthTime(preset.value);
                setTimeUnknown(false);
              }}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="field-card">
        <h3>3. 국가와 도시</h3>
        <p className="helper-text">
          주요 도시는 timezone을 바로 적용하고, 목록에 없는 도시는 백엔드가 좌표와 timezone을 다시 계산합니다.
        </p>

        <label>
          국가
          <select name="country" value={country} onChange={handleCountryChange}>
            {COUNTRY_OPTIONS.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          도시
          <input
            type="text"
            name="city"
            list="city-options"
            value={city}
            onChange={(event) => setCity(event.target.value)}
            placeholder="예: 서울, 부산, Tokyo"
            required
          />
          <datalist id="city-options">
            {cityOptions.map((option) => (
              <option key={`${option.countryCode}-${option.city}`} value={option.city}>
                {option.note}
              </option>
            ))}
          </datalist>
        </label>

        {isKnownCity ? <input type="hidden" name="timezone" value={timezone} /> : null}

        <div className="note-box">
          <strong>{isKnownCity ? "현재 적용 timezone:" : "직접 입력 도시 처리:"}</strong>{" "}
          {isKnownCity ? timezone : "백엔드에서 좌표와 timezone을 다시 계산합니다."}
          <br />
          {isKnownCity
            ? "자주 쓰는 도시는 고정 timezone을 적용해 더 안정적으로 처리합니다."
            : "도시명이 정확할수록 차트와 운세 결과가 좋아집니다."}
        </div>
      </div>

      <div className="button-row full-width">
        <button type="submit">{submitLabel}</button>
        {secondarySubmitAction && secondarySubmitLabel ? (
          <button type="submit" className="secondary-button" formAction={secondarySubmitAction}>
            {secondarySubmitLabel}
          </button>
        ) : null}
      </div>
    </form>
  );
}
