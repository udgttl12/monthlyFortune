import Link from "next/link";
import CopyResultsButton from "@/components/CopyResultsButton";
import FloatingMenu from "@/components/FloatingMenu";
import {
  DateInsightList,
  EvidenceList,
  MonthOverviewCard
} from "@/components/HoroscopeReportParts";
import YongyongMascot from "@/components/YongyongMascot";
import {
  type HoroscopeSearchParams,
  type MonthlyHoroscopeResponse,
  type YearlyHoroscopeResponse,
  buildHoroscopeApiParams,
  buildHoroscopePageHref,
  getSelectedHoroscopeMonth,
  getSelectedHoroscopeYear,
  hasRequiredBirthDetails
} from "@/app/lib/horoscope";
import {
  buildCalendarPageHref,
  buildCoachPageHref,
  buildTodayPageHref,
  getTodayInKorea
} from "@/app/lib/aiRetention";
import { buildFloatingMenuItems } from "@/app/lib/floatingMenu";
import { buildHoroscopeResultText } from "@/app/lib/resultText";

const API_BASE_URL = process.env.MONTHLY_FORTUNE_API_URL ?? "http://127.0.0.1:8000";

type HoroscopeSectionsProps = {
  readonly searchParams: HoroscopeSearchParams;
};

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
  const floatingMenuItems = buildFloatingMenuItems({
    page: "horoscope",
    searchParams,
    selectedYear,
    selectedMonth,
    hasCopyText: Boolean(yearly && monthly)
  });

  if (!yearly || !monthly) {
    return (
      <div className="stack">
        <article className="card section-card recovery-card">
          <span className="eyebrow">월운을 잠시 불러오지 못했어요</span>
          <h2>입력 정보와 백엔드 상태를 확인해 주세요.</h2>
          <p>
            FastAPI 서버가 실행 중인지 확인하거나, 출생 정보와 조회 연도/월을 다시 입력해 주세요.
            화면은 비워두지 않고 바로 회복할 수 있는 길을 남겨둘게요.
          </p>
          <div className="button-row">
            <a className="button-link" href="#birth-details">
              입력 수정
            </a>
            <a className="button-link" href="/">
              처음부터 다시
            </a>
          </div>
        </article>
        <FloatingMenu items={floatingMenuItems} />
      </div>
    );
  }

  const selectedOverview = yearly.months.find((item) => item.month === selectedMonth);
  const horoscopeResultText = buildHoroscopeResultText({
    searchParams,
    yearly,
    monthly,
    selectedMonth
  });
  const todayHref = buildTodayPageHref(searchParams, getTodayInKorea());
  const calendarHref = buildCalendarPageHref(searchParams, selectedYear, selectedMonth);
  const coachHref = buildCoachPageHref(searchParams, selectedYear, selectedMonth);

  return (
    <div className="stack">
      <section className="card hero-card horoscope-result-hero monthly-report-hero">
        <div className="report-hero-main">
          <span className="eyebrow">점성술로 보는 나만의 월운</span>
          <h1>
            {monthly.year}년 {monthly.month}월, 나만의 월운
          </h1>
          <p className="muted hero-copy">{monthly.summary}</p>
          <div className="report-status-row">
            <span className={`query-pill ${monthly.llmEnhanced ? "active" : ""}`}>
              {monthly.llmEnhanced ? "AI 보강" : "기본 계산"}
            </span>
            <span className="query-pill">{yearly.year}년 흐름 기반</span>
          </div>
          <div className="report-action-row">
            <Link className="button-link" href={todayHref}>
              오늘 브리핑
            </Link>
            <Link className="button-link" href={coachHref}>
              AI 코치에게 묻기
            </Link>
            <Link className="button-link subtle" href={calendarHref}>
              날짜 흐름 보기
            </Link>
          </div>
        </div>
        <div className="report-hero-side">
          <YongyongMascot variant="report" caption="이번 달 흐름을 수정구슬에 비춰봤어요." />
          <CopyResultsButton text={horoscopeResultText} />
        </div>
      </section>

      <section className="card monthly-highlight monthly-core-panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">이번 달 핵심</span>
            <h2>{selectedOverview?.topTheme ?? "이번 달의 리듬을 차분히 확인해 보세요."}</h2>
            <p className="muted">{yearly.profileSummary}</p>
          </div>
          {selectedOverview ? <span className="query-pill">흐름 강도 {selectedOverview.intensityScore}/10</span> : null}
        </div>

        {selectedOverview ? (
          <div className="horoscope-summary-strip">
            <div>
              <span>좋은 구간</span>
              <strong>{selectedOverview.luckyWindow.label}</strong>
            </div>
            <div>
              <span>주의 구간</span>
              <strong>{selectedOverview.cautionWindow.label}</strong>
            </div>
            <div>
              <span>집중 영역</span>
              <strong>{selectedOverview.focusAreas.join(" · ")}</strong>
            </div>
            <div>
              <span>이번 달 제목</span>
              <strong>{selectedOverview.title}</strong>
            </div>
          </div>
        ) : null}
      </section>

      <div className="section-grid two-column-grid priority-date-grid">
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

      <section className="card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">분야별 상세</span>
            <h2>이번 달을 실제 생활로 읽기</h2>
            <p className="muted">월운을 커리어, 돈, 관계, 컨디션으로 나누어 실행 가능한 언어로 정리했습니다.</p>
          </div>
        </div>

        <div className="section-grid two-column-grid report-section-grid">
          <article className="section-card compact-stack">
            <h3>커리어</h3>
            <p>{monthly.sections.career}</p>
          </article>
          <article className="section-card compact-stack">
            <h3>재정</h3>
            <p>{monthly.sections.money}</p>
          </article>
          <article className="section-card compact-stack">
            <h3>관계</h3>
            <p>{monthly.sections.love}</p>
          </article>
          <article className="section-card compact-stack">
            <h3>컨디션</h3>
            <p>{monthly.sections.risk}</p>
          </article>
        </div>
      </section>

      <section className="card yearly-strip-panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">12개월 흐름</span>
            <h2>다른 달의 리듬도 이어서 보기</h2>
            <p className="muted">궁금한 달을 누르면 월운 리포트가 해당 월로 바뀝니다.</p>
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

      <EvidenceList items={monthly.evidence} />
      <FloatingMenu items={floatingMenuItems} copyText={horoscopeResultText} />
    </div>
  );
}
