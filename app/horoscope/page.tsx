import { Suspense } from "react";
import BirthDetailsForm from "@/components/BirthDetailsForm";
import HoroscopeSections from "@/components/HoroscopeSections";
import Spinner from "@/components/Spinner";
import {
  HoroscopeSearchParams,
  getSelectedHoroscopeYear,
  hasRequiredBirthDetails
} from "@/app/lib/horoscope";

export const dynamic = "force-dynamic";

interface HoroscopePageProps {
  searchParams: HoroscopeSearchParams;
}

export default function HoroscopePage({ searchParams }: HoroscopePageProps) {
  const hasBirthDetails = hasRequiredBirthDetails(searchParams);
  const selectedYear = getSelectedHoroscopeYear(searchParams);
  const isTimeEstimated = searchParams.timeUnknown === "true";

  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">개인 맞춤 연간/월간 운세</span>
        <h1>한 해의 흐름을 먼저 보고, 궁금한 달을 깊게 읽어보세요.</h1>
        <p className="muted hero-copy">
          연간 개요에서는 12개월의 흐름을 비교하고, 월 상세에서는 좋은 날짜, 주의 날짜, 핵심 근거와 함께
          보다 구체적인 리딩을 확인할 수 있습니다.
        </p>
      </section>

      <section className="card">
        <div className="section-heading">
          <div>
            <h2>개인 운세 조회</h2>
            <p className="muted">
              출생 정보와 조회 연도를 입력하면 연간 개요를 먼저 보여주고, 선택한 달의 상세 리딩을 이어서
              제공합니다.
            </p>
          </div>
        </div>

        <BirthDetailsForm
          action="/horoscope"
          submitLabel="연간 운세 보기"
          secondarySubmitAction="/chart"
          secondarySubmitLabel="출생 차트 보기"
          showYearField
          defaultYear={selectedYear}
        />
      </section>

      {isTimeEstimated && hasBirthDetails ? (
        <section className="card warning-card">
          <h2>출생 시간이 추정값입니다</h2>
          <p>
            현재 운세는 정오 12:00 기준으로 계산했습니다. 월별 큰 흐름은 참고할 수 있지만, 날짜 단위 리딩과
            세부 해석은 실제 시간에 따라 달라질 수 있습니다.
          </p>
        </section>
      ) : null}

      {!hasBirthDetails ? (
        <section className="card info-card">
          <h2>먼저 출생 정보를 입력해 주세요</h2>
          <p>
            이 화면은 출생 차트를 바탕으로 연간 개요와 월 상세 운세를 함께 보여줍니다. 위 폼을 채우면 바로
            결과를 계산합니다.
          </p>
        </section>
      ) : (
        <Suspense fallback={<Spinner />}>
          <HoroscopeSections searchParams={searchParams} />
        </Suspense>
      )}
    </div>
  );
}
