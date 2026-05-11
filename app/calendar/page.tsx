import { Suspense } from "react";
import ActionCalendarSections from "@/components/ActionCalendarSections";
import BirthDetailsForm from "@/components/BirthDetailsForm";
import Spinner from "@/components/Spinner";
import {
  HoroscopeSearchParams,
  getSelectedHoroscopeMonth,
  getSelectedHoroscopeYear,
  hasRequiredBirthDetails
} from "@/app/lib/horoscope";

export const dynamic = "force-dynamic";

interface CalendarPageProps {
  searchParams: HoroscopeSearchParams;
}

export default function CalendarPage({ searchParams }: CalendarPageProps) {
  const hasBirthDetails = hasRequiredBirthDetails(searchParams);
  const selectedYear = getSelectedHoroscopeYear(searchParams);
  const selectedMonth = getSelectedHoroscopeMonth(selectedYear, searchParams.month);

  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">AI 월간 액션 캘린더</span>
        <h1>이번 달 움직일 날과 쉬어갈 날을 한눈에 봅니다</h1>
        <p className="muted hero-copy">
          출생 차트와 월간 흐름을 바탕으로 매일의 행동, 피할 선택, 판단 근거를 정리합니다.
        </p>
      </section>

      <section className="card" id="birth-details">
        <div className="section-heading">
          <div>
            <h2>출생 정보</h2>
            <p className="muted">정확한 월간 타이밍을 위해 생년월일, 시간, 도시를 입력해 주세요.</p>
          </div>
        </div>
        <BirthDetailsForm action="/calendar" submitLabel="액션 캘린더 보기" showYearField defaultYear={selectedYear} />
      </section>

      {hasBirthDetails ? (
        <Suspense fallback={<Spinner />}>
          <ActionCalendarSections searchParams={searchParams} year={selectedYear} month={selectedMonth} />
        </Suspense>
      ) : null}
    </div>
  );
}
