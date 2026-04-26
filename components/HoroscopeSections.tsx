import Link from "next/link";
import type { Route } from "next";
import {
  HoroscopeDateInsight,
  HoroscopeEvidence,
  HoroscopeSearchParams,
  MonthlyHoroscopeResponse,
  YearlyHoroscopeMonth,
  YearlyHoroscopeResponse,
  buildHoroscopeApiParams,
  buildHoroscopePageHref,
  formatHoroscopeDate,
  getSelectedHoroscopeMonth,
  getSelectedHoroscopeYear,
  hasRequiredBirthDetails
} from "@/app/lib/horoscope";

const API_BASE_URL = process.env.MONTHLY_FORTUNE_API_URL ?? "http://127.0.0.1:8000";

interface HoroscopeSectionsProps {
  searchParams: HoroscopeSearchParams;
}

async function getYearlyHoroscope(
  searchParams: HoroscopeSearchParams,
  selectedYear: number
): Promise<YearlyHoroscopeResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/horoscope/yearly?${buildHoroscopeApiParams(searchParams, selectedYear).toString()}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

async function getMonthlyHoroscope(
  searchParams: HoroscopeSearchParams,
  selectedYear: number,
  selectedMonth: number
): Promise<MonthlyHoroscopeResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/horoscope/monthly?${buildHoroscopeApiParams(
        searchParams,
        selectedYear,
        selectedMonth
      ).toString()}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

function MonthOverviewCard({
  item,
  active,
  href
}: {
  item: YearlyHoroscopeMonth;
  active: boolean;
  href: Route;
}) {
  return (
    <Link className={`month-card${active ? " active" : ""}`} href={href}>
      <div className="month-card-top">
        <strong>{item.month}월</strong>
        <span className="score-pill">강도 {item.intensityScore}/10</span>
      </div>
      <h3>{item.title}</h3>
      <p className="muted">{item.topTheme}</p>
      <div className="tag-row">
        {item.focusAreas.map((area) => (
          <span key={`${item.month}-${area}`} className="tag">
            {area}
          </span>
        ))}
      </div>
      <div className="window-copy">
        <p>
          <strong>좋은 흐름</strong> {item.luckyWindow.label}
        </p>
        <p>
          <strong>주의 구간</strong> {item.cautionWindow.label}
        </p>
      </div>
    </Link>
  );
}

function DateInsightList({
  title,
  items,
  tone
}: {
  title: string;
  items: HoroscopeDateInsight[];
  tone: "positive" | "negative";
}) {
  return (
    <article className="card section-card">
      <h2>{title}</h2>
      <div className={`date-insight-list ${tone}`}>
        {items.map((item) => (
          <article key={`${title}-${item.date}`} className="date-insight-item">
            <strong>{formatHoroscopeDate(item.date)}</strong>
            <p className="date-insight-label">{item.label}</p>
            <p>{item.reason}</p>
          </article>
        ))}
      </div>
    </article>
  );
}

function EvidenceList({ items }: { items: HoroscopeEvidence[] }) {
  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <h2>핵심 근거</h2>
          <p className="muted">이번 달 리딩을 만들 때 강하게 잡힌 트랜짓과 포인트입니다.</p>
        </div>
      </div>

      <div className="evidence-grid">
        {items.map((item) => (
          <article key={`${item.date}-${item.headline}`} className={`evidence-card ${item.tone}`}>
            <span className="evidence-date">{formatHoroscopeDate(item.date)}</span>
            <h3>{item.headline}</h3>
            <p>{item.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default async function HoroscopeSections({ searchParams }: HoroscopeSectionsProps) {
  if (!hasRequiredBirthDetails(searchParams)) {
    return null;
  }

  const selectedYear = getSelectedHoroscopeYear(searchParams);
  const selectedMonth = getSelectedHoroscopeMonth(selectedYear, searchParams.month);
  const [yearly, monthly] = await Promise.all([
    getYearlyHoroscope(searchParams, selectedYear),
    getMonthlyHoroscope(searchParams, selectedYear, selectedMonth)
  ]);

  if (!yearly || !monthly) {
    return (
      <article className="card section-card">
        <h2>운세를 불러오지 못했습니다</h2>
        <p>
          FastAPI 서버가 실행 중인지, 그리고 입력한 출생 정보와 도시명이 올바른지 확인해 주세요.
        </p>
      </article>
    );
  }

  return (
    <div className="stack">
      <section className="card">
        <div className="section-heading">
          <div>
            <h2>{yearly.year}년 연간 개요</h2>
            <p className="muted">{yearly.profileSummary}</p>
          </div>
          <span className="query-pill">{selectedMonth}월 상세 보기</span>
        </div>

        <div className="month-grid">
          {yearly.months.map((item) => (
            <MonthOverviewCard
              key={item.month}
              item={item}
              active={item.month === selectedMonth}
              href={buildHoroscopePageHref(searchParams, selectedYear, item.month)}
            />
          ))}
        </div>
      </section>

      <section className="card">
        <div className="section-heading">
          <div>
            <h2>
              {monthly.year}년 {monthly.month}월 상세 리딩
            </h2>
            <p className="muted">{monthly.summary}</p>
          </div>
          <span className={`query-pill ${monthly.llmEnhanced ? "active" : ""}`}>
            {monthly.llmEnhanced ? "AI 확장 리딩" : "기본 리딩"}
          </span>
        </div>
      </section>

      <div className="section-grid two-column-grid">
        <article className="card section-card">
          <h2>커리어</h2>
          <p>{monthly.sections.career}</p>
        </article>
        <article className="card section-card">
          <h2>재정</h2>
          <p>{monthly.sections.money}</p>
        </article>
        <article className="card section-card">
          <h2>관계</h2>
          <p>{monthly.sections.love}</p>
        </article>
        <article className="card section-card">
          <h2>리스크</h2>
          <p>{monthly.sections.risk}</p>
        </article>
      </div>

      <div className="section-grid two-column-grid">
        <DateInsightList title="좋은 날짜" items={monthly.luckyDates} tone="positive" />
        <DateInsightList title="주의 날짜" items={monthly.cautionDates} tone="negative" />
      </div>

      <EvidenceList items={monthly.evidence} />
    </div>
  );
}
