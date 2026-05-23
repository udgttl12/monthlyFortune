import Link from "next/link";
import type { Route } from "next";
import CopyResultsButton from "@/components/CopyResultsButton";
import FloatingMenu from "@/components/FloatingMenu";
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
import { buildFloatingMenuItems } from "@/app/lib/floatingMenu";
import { buildHoroscopeResultText } from "@/app/lib/resultText";

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
          <strong>좋은 구간</strong> {item.luckyWindow.label}
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
  description,
  items,
  tone
}: {
  title: string;
  description: string;
  items: HoroscopeDateInsight[];
  tone: "positive" | "negative";
}) {
  return (
    <article className="card section-card">
      <h2>{title}</h2>
      <p className="muted section-description">{description}</p>
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
          <h2>해석 근거</h2>
          <p className="muted">이번 달 리딩에 크게 반영된 주요 트랜싯과 사인입니다.</p>
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
          FastAPI 서버가 실행 중인지, 입력한 출생 정보와 조회 연도/월이 올바른지 확인해 주세요.
        </p>
      </article>
    );
  }

  const selectedOverview = yearly.months.find((item) => item.month === selectedMonth);
  const horoscopeResultText = buildHoroscopeResultText({
    searchParams,
    yearly,
    monthly,
    selectedMonth
  });
  const floatingMenuItems = buildFloatingMenuItems({
    page: "horoscope",
    searchParams,
    hasCopyText: true,
    selectedYear,
    selectedMonth
  });

  return (
    <div className="stack">
      <section className="card hero-card horoscope-result-hero">
        <div>
          <span className="eyebrow">연간 운세 결과</span>
          <h1>{yearly.year}년 흐름 요약</h1>
          <p className="muted hero-copy">{yearly.profileSummary}</p>
        </div>
        <div className="result-toolbar">
          <CopyResultsButton text={horoscopeResultText} />
        </div>
      </section>

      <section className="card monthly-highlight">
        <div className="section-heading">
          <div>
            <span className="eyebrow">선택한 달</span>
            <h2>
              {monthly.year}년 {monthly.month}월 상세 리딩
            </h2>
            <p className="muted">{monthly.summary}</p>
          </div>
          <span className={`query-pill ${monthly.llmEnhanced ? "active" : ""}`}>
            {monthly.llmEnhanced ? "AI 보강" : "기본 계산"}
          </span>
        </div>

        {selectedOverview ? (
          <div className="horoscope-summary-strip">
            <div>
              <span>이번 달 주제</span>
              <strong>{selectedOverview.topTheme}</strong>
            </div>
            <div>
              <span>흐름 강도</span>
              <strong>{selectedOverview.intensityScore}/10</strong>
            </div>
            <div>
              <span>좋은 구간</span>
              <strong>{selectedOverview.luckyWindow.label}</strong>
            </div>
            <div>
              <span>주의 구간</span>
              <strong>{selectedOverview.cautionWindow.label}</strong>
            </div>
          </div>
        ) : null}
      </section>

      <section className="card">
        <div className="section-heading">
          <div>
            <h2>12개월 흐름</h2>
            <p className="muted">궁금한 달을 누르면 위의 상세 리딩이 해당 월로 바뀝니다.</p>
          </div>
          <span className="query-pill">{selectedMonth}월 보는 중</span>
        </div>

        <div className="month-grid compact-month-grid">
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
          <h2>컨디션</h2>
          <p>{monthly.sections.risk}</p>
        </article>
      </div>

      <div className="section-grid two-column-grid">
        <DateInsightList
          title="좋은 날짜"
          description="시작, 연락, 조정처럼 힘을 실어도 좋은 날입니다."
          items={monthly.luckyDates}
          tone="positive"
        />
        <DateInsightList
          title="주의 날짜"
          description="속도 조절과 확인이 필요한 날입니다."
          items={monthly.cautionDates}
          tone="negative"
        />
      </div>

      <EvidenceList items={monthly.evidence} />
      <FloatingMenu items={floatingMenuItems} copyText={horoscopeResultText} />
    </div>
  );
}
