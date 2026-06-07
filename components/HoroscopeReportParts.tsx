import Link from "next/link";
import type { Route } from "next";
import type {
  HoroscopeDateInsight,
  HoroscopeEvidence,
  YearlyHoroscopeMonth
} from "@/app/lib/horoscope";
import { formatHoroscopeDate } from "@/app/lib/horoscope";

type MonthOverviewCardProps = {
  readonly item: YearlyHoroscopeMonth;
  readonly active: boolean;
  readonly href: Route;
};

export function MonthOverviewCard({ item, active, href }: MonthOverviewCardProps) {
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

type DateInsightListProps = {
  readonly title: string;
  readonly description: string;
  readonly items: readonly HoroscopeDateInsight[];
  readonly tone: "positive" | "negative";
};

export function DateInsightList({ title, description, items, tone }: DateInsightListProps) {
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

type EvidenceListProps = {
  readonly items: readonly HoroscopeEvidence[];
};

export function EvidenceList({ items }: EvidenceListProps) {
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
