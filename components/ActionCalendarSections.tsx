import Link from "next/link";
import type { HoroscopeSearchParams } from "@/app/lib/horoscope";
import {
  buildCoachPageHref,
  buildTodayPageHref,
  fetchActionCalendar
} from "@/app/lib/aiRetention";

interface ActionCalendarSectionsProps {
  searchParams: HoroscopeSearchParams;
  year: number;
  month: number;
}

export default async function ActionCalendarSections({
  searchParams,
  year,
  month
}: ActionCalendarSectionsProps) {
  const calendar = await fetchActionCalendar(searchParams, year, month);

  if (!calendar) {
    return (
      <article className="card section-card">
        <h2>액션 캘린더를 불러오지 못했습니다</h2>
        <p>백엔드가 실행 중인지 확인한 뒤 다시 시도해 주세요.</p>
      </article>
    );
  }

  return (
    <div className="stack">
      <section className="card">
        <div className="section-heading">
          <div>
            <h2>
              {calendar.year}년 {calendar.month}월 액션 캘린더
            </h2>
            <p className="muted">{calendar.profileSummary}</p>
          </div>
          <span className={`query-pill ${calendar.llmEnhanced ? "active" : ""}`}>
            {calendar.llmEnhanced ? "AI 액션 캘린더" : "기본 액션 캘린더"}
          </span>
        </div>

        <div className="action-calendar-grid">
          {calendar.days.map((day) => (
            <article key={day.date} className={`action-day-card ${day.tone}`}>
              <div className="month-card-top">
                <strong>{day.date.slice(5).replace("-", "/")}</strong>
                <span className="score-pill">{day.score}/10</span>
              </div>
              <h3>{day.title}</h3>
              <p>{day.action}</p>
              <p className="muted">{day.avoid}</p>
              <div className="tag-row">
                {day.categories.map((category) => (
                  <span key={`${day.date}-${category}`} className="tag">
                    {category}
                  </span>
                ))}
              </div>
              <Link className="inline-link" href={buildTodayPageHref(searchParams, day.date)}>
                오늘 브리핑
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section className="card section-card">
        <h2>결정이 필요한 일이 있나요?</h2>
        <p>면접, 계약, 고백, 화해, 지출처럼 날짜를 고르고 싶은 일을 AI 코치에게 물어보세요.</p>
        <Link className="button-link" href={buildCoachPageHref(searchParams, year, month)}>
          AI 코치에게 질문하기
        </Link>
      </section>
    </div>
  );
}
