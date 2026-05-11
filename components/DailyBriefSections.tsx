import Link from "next/link";
import type { HoroscopeSearchParams } from "@/app/lib/horoscope";
import { buildCalendarPageHref, buildCoachPageHref, fetchDailyBrief } from "@/app/lib/aiRetention";

interface DailyBriefSectionsProps {
  searchParams: HoroscopeSearchParams;
  year: number;
  month: number;
  targetDate: string;
}

export default async function DailyBriefSections({
  searchParams,
  year,
  month,
  targetDate
}: DailyBriefSectionsProps) {
  const brief = await fetchDailyBrief(searchParams, year, month, targetDate);

  if (!brief) {
    return (
      <article className="card section-card">
        <h2>오늘 브리핑을 불러오지 못했습니다</h2>
        <p>백엔드가 실행 중인지 확인한 뒤 다시 시도해 주세요.</p>
      </article>
    );
  }

  return (
    <div className="stack">
      <section className={`card daily-brief-card ${brief.tone}`}>
        <div className="section-heading">
          <div>
            <h2>{brief.date} 오늘의 브리핑</h2>
            <p className="muted">{brief.summary}</p>
          </div>
          <span className="score-pill">{brief.score}/10</span>
        </div>
        <h3>{brief.headline}</h3>
      </section>

      <div className="section-grid two-column-grid">
        <article className="card section-card">
          <h2>오늘 할 일</h2>
          <p>{brief.action}</p>
        </article>
        <article className="card section-card">
          <h2>오늘 피할 일</h2>
          <p>{brief.avoid}</p>
        </article>
        <article className="card section-card">
          <h2>좋은 시간대</h2>
          <p>{brief.bestTimeHint}</p>
        </article>
        <article className="card section-card">
          <h2>주의 시간대</h2>
          <p>{brief.avoidTimeHint}</p>
        </article>
      </div>

      <section className="card section-card">
        <h2>저녁 회고</h2>
        <p>{brief.reflectionPrompt}</p>
      </section>

      <div className="result-toolbar link-toolbar">
        <Link className="button-link" href={buildCalendarPageHref(searchParams, year, month)}>
          월간 캘린더
        </Link>
        <Link className="button-link" href={buildCoachPageHref(searchParams, year, month)}>
          AI 코치
        </Link>
      </div>
    </div>
  );
}
