import BirthDetailsForm from "@/components/BirthDetailsForm";
import CoachPanel from "@/components/CoachPanel";
import {
  HoroscopeSearchParams,
  getSelectedHoroscopeMonth,
  getSelectedHoroscopeYear,
  hasRequiredBirthDetails
} from "@/app/lib/horoscope";

export const dynamic = "force-dynamic";

interface CoachPageProps {
  searchParams: HoroscopeSearchParams;
}

export default function CoachPage({ searchParams }: CoachPageProps) {
  const hasBirthDetails = hasRequiredBirthDetails(searchParams);
  const selectedYear = getSelectedHoroscopeYear(searchParams);
  const selectedMonth = getSelectedHoroscopeMonth(selectedYear, searchParams.month);

  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">AI 결정 타이밍 코치</span>
        <h1>중요한 선택을 언제 어떻게 움직일지 물어보세요</h1>
        <p className="muted hero-copy">
          면접, 계약, 고백, 화해, 지출, 이직처럼 날짜와 행동이 필요한 질문에 답합니다.
        </p>
      </section>

      <section className="card" id="birth-details">
        <div className="section-heading">
          <div>
            <h2>출생 정보</h2>
            <p className="muted">질문은 개인 차트와 이번 달 일별 흐름에 연결됩니다.</p>
          </div>
        </div>
        <BirthDetailsForm action="/coach" submitLabel="코치 준비하기" showYearField defaultYear={selectedYear} />
      </section>

      {hasBirthDetails ? <CoachPanel searchParams={searchParams} year={selectedYear} month={selectedMonth} /> : null}
    </div>
  );
}
