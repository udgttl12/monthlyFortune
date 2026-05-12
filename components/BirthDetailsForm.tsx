"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { readLastViewedBirthDetails, writeLastViewedBirthDetails } from "@/app/lib/birthDetailsStorage";
import { normalizeBirthDateInput, parseBirthDateInput } from "@/app/lib/birthDateInput";
import { normalizeBirthTimeInput, parseBirthTimeInput } from "@/app/lib/birthTimeInput";
import {
  COUNTRY_OPTIONS,
  getCitiesByCountry,
  getDefaultTimezone,
  getLocationOption,
  getSelectableCity
} from "@/app/lib/locations";

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
  const [city, setCity] = useState(() => getSelectableCity(undefined, "KR"));
  const [birthDateInput, setBirthDateInput] = useState("");
  const [birthDateSubmitError, setBirthDateSubmitError] = useState("");
  const [birthTimeInput, setBirthTimeInput] = useState("1200");
  const [birthTimeSubmitError, setBirthTimeSubmitError] = useState("");
  const [timeUnknown, setTimeUnknown] = useState(false);
  const [year, setYear] = useState(defaultYear);

  const birthDate = parseBirthDateInput(birthDateInput) ?? "";
  const parsedBirthTime = parseBirthTimeInput(birthTimeInput);
  const birthTime = timeUnknown ? "12:00" : parsedBirthTime ?? "";
  const birthDateError =
    birthDateInput.length === 8 && !birthDate ? "존재하는 생년월일을 입력해 주세요." : birthDateSubmitError;
  const birthTimeError =
    !timeUnknown && birthTimeInput.length === 4 && !parsedBirthTime
      ? "존재하는 출생 시간을 입력해 주세요."
      : birthTimeSubmitError;
  const cityOptions = getCitiesByCountry(country);
  const matchedLocation = getLocationOption(city, country);
  const timezone = matchedLocation?.timezone ?? getDefaultTimezone(country);

  useEffect(() => {
    const stored = readLastViewedBirthDetails(window.localStorage);

    if (!stored) {
      return;
    }

    const storedCountry = COUNTRY_OPTIONS.some((option) => option.code === stored.country)
      ? stored.country
      : "KR";

    setBirthDateInput(stored.birthDateInput);
    setBirthTimeInput(stored.birthTimeInput || "1200");
    setCountry(storedCountry);
    setCity(getSelectableCity(stored.city, storedCountry));
    setTimeUnknown(stored.timeUnknown);
    setYear(stored.year);
  }, []);

  function handleBirthDateChange(event: ChangeEvent<HTMLInputElement>) {
    setBirthDateInput(normalizeBirthDateInput(event.target.value));
    setBirthDateSubmitError("");
  }

  function handleBirthTimeChange(event: ChangeEvent<HTMLInputElement>) {
    setBirthTimeInput(normalizeBirthTimeInput(event.target.value));
    setBirthTimeSubmitError("");
  }

  function handleCountryChange(event: ChangeEvent<HTMLSelectElement>) {
    const nextCountry = event.target.value;

    setCountry(nextCountry);
    setCity(getSelectableCity(undefined, nextCountry));
  }

  function handleCityChange(event: ChangeEvent<HTMLSelectElement>) {
    setCity(event.target.value);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    const hasValidBirthDate = Boolean(birthDate);
    const hasValidBirthTime = timeUnknown || Boolean(parsedBirthTime);

    if (!hasValidBirthDate) {
      setBirthDateSubmitError(
        birthDateInput.length === 8 ? "존재하는 생년월일을 입력해 주세요." : "생년월일 8자리를 입력해 주세요."
      );
    }

    if (!hasValidBirthTime) {
      setBirthTimeSubmitError(
        birthTimeInput.length === 4 ? "존재하는 출생 시간을 입력해 주세요." : "출생 시간 4자리를 입력해 주세요."
      );
    }

    if (!hasValidBirthDate || !hasValidBirthTime) {
      event.preventDefault();
      return;
    }

    writeLastViewedBirthDetails(window.localStorage, {
      birthDateInput,
      birthTimeInput: timeUnknown ? "1200" : birthTimeInput,
      city,
      country,
      timeUnknown,
      year
    });
  }

  function handleTimeUnknownChange(event: ChangeEvent<HTMLInputElement>) {
    const checked = event.target.checked;

    setTimeUnknown(checked);
    setBirthTimeSubmitError("");

    if (checked) {
      setBirthTimeInput("1200");
    }
  }

  return (
    <form className="form-grid" action={action} method="GET" onSubmit={handleSubmit}>
      <div className="field-card full-width">
        <h3>1. 생년월일</h3>
        <p className="helper-text">
          날짜와 시간은 개인 차트 계산의 기준입니다. 생년월일은 숫자 8자리로 입력해 주세요.
        </p>
        <div className="field-grid">
          <label>
            생년월일
            <input
              type="text"
              value={birthDateInput}
              onChange={handleBirthDateChange}
              inputMode="numeric"
              autoComplete="bday"
              placeholder="예: 19940718"
              maxLength={8}
              pattern="[0-9]{8}"
              aria-invalid={birthDateError ? "true" : undefined}
              aria-describedby="birth-date-hint birth-date-error"
              required
            />
            <input type="hidden" name="birthDate" value={birthDate} />
            <span id="birth-date-hint" className="input-hint">
              하이픈 없이 숫자 8자리
            </span>
            {birthDateError ? (
              <span id="birth-date-error" className="field-error">
                {birthDateError}
              </span>
            ) : null}
          </label>

          {showYearField ? (
            <label>
              확인할 연도
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
          시간을 모르면 12:00 기준으로 계산합니다. 다만 상승궁과 하우스 해석은 실제 시간에 가까울수록 더 정확합니다.
        </p>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={timeUnknown}
            onChange={handleTimeUnknownChange}
          />
          출생 시간을 모릅니다
        </label>

        <input type="hidden" name="birthTime" value={birthTime} />
        <input type="hidden" name="timeUnknown" value={timeUnknown ? "true" : "false"} />

        <label>
          출생 시간
          <input
            type="text"
            value={birthTimeInput}
            onChange={handleBirthTimeChange}
            inputMode="numeric"
            autoComplete="off"
            placeholder="예: 0930"
            maxLength={4}
            pattern="[0-9]{4}"
            aria-invalid={birthTimeError ? "true" : undefined}
            aria-describedby="birth-time-hint birth-time-error"
            disabled={timeUnknown}
            required={!timeUnknown}
          />
          <span id="birth-time-hint" className="input-hint">
            하이픈 없이 숫자 4자리
          </span>
          {birthTimeError ? (
            <span id="birth-time-error" className="field-error">
              {birthTimeError}
            </span>
          ) : null}
        </label>
      </div>

      <div className="field-card">
        <h3>3. 국가와 도시</h3>
        <p className="helper-text">
          국가를 선택하면 해당 국가의 등록 도시만 고를 수 있습니다. 도시별 timezone은 자동으로 함께 전달됩니다.
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
          <select name="city" value={city} onChange={handleCityChange} required>
            {cityOptions.map((option) => (
              <option key={`${option.countryCode}-${option.city}`} value={option.city}>
                {option.city} · {option.note}
              </option>
            ))}
          </select>
        </label>

        <input type="hidden" name="timezone" value={timezone} />

        <div className="note-box">
          <strong>선택 도시 기준 timezone:</strong> {timezone}
          <br />
          목록에 필요한 도시가 없으면 이후 등록 도시 목록에 추가할 수 있습니다.
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
