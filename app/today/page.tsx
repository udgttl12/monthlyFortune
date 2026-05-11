import { Suspense } from "react";
import BirthDetailsForm from "@/components/BirthDetailsForm";
import DailyBriefSections from "@/components/DailyBriefSections";
import Spinner from "@/components/Spinner";
import { AiRetentionSearchParams, getTodayInKorea } from "@/app/lib/aiRetention";
import {
  getSelectedHoroscopeMonth,
  getSelectedHoroscopeYear,
  hasRequiredBirthDetails
} from "@/app/lib/horoscope";

export const dynamic = "force-dynamic";

interface TodayPageProps {
  searchParams: AiRetentionSearchParams;
}

export default function TodayPage({ searchParams }: TodayPageProps) {
  const hasBirthDetails = hasRequiredBirthDetails(searchParams);
  const targetDate = searchParams.targetDate ?? getTodayInKorea();
  const selectedYear = getSelectedHoroscopeYear({ ...searchParams, year: searchParams.year ?? targetDate.slice(0, 4) });
  const selectedMonth = searchParams.month
    ? getSelectedHoroscopeMonth(selectedYear, searchParams.month)
    : Number(targetDate.slice(5, 7));

  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">AI 오늘 브리핑</span>
        <h1>오늘 움직일 방식만 짧고 분명하게 봅니다</h1>
        <p className="muted hero-copy">
          매일 아침 확인할 수 있도록 오늘의 행동, 주의점, 회고 질문을 정리합니다.
        </p>
      </section>

      <section className="card" id="birth-details">
        <div className="section-heading">
          <div>
            <h2>출생 정보</h2>
            <p className="muted">오늘의 흐름을 개인 차트에 맞춰 계산합니다.</p>
          </div>
        </div>
        <BirthDetailsForm action="/today" submitLabel="오늘 브리핑 보기" showYearField defaultYear={selectedYear} />
      </section>

      {hasBirthDetails ? (
        <Suspense fallback={<Spinner />}>
          <DailyBriefSections
            searchParams={searchParams}
            year={selectedYear}
            month={selectedMonth}
            targetDate={targetDate}
          />
        </Suspense>
      ) : null}
    </div>
  );
}
