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

  if (hasBirthDetails) {
    return (
      <div className="stack">
        <Suspense fallback={<Spinner />}>
          <HoroscopeSections searchParams={searchParams} />
        </Suspense>

        {isTimeEstimated ? (
          <section className="card warning-card">
            <h2>출생 시간이 추정값입니다</h2>
            <p>
              현재 운세는 정오 12:00 기준으로 계산했습니다. 월별 흐름과 날짜 범위는 참고할 수 있지만,
              상승궁과 하우스 기반 해석은 실제 출생 시간에 따라 달라질 수 있습니다.
            </p>
          </section>
        ) : null}

        <section className="card" id="birth-details">
          <div className="section-heading">
            <div>
              <span className="eyebrow">입력 수정</span>
              <h2>출생 정보나 조회 연도를 바꾸기</h2>
              <p className="muted">
                결과를 먼저 보여주고, 수정이 필요할 때만 이 영역에서 다시 조회하도록 배치했습니다.
              </p>
            </div>
          </div>

          <BirthDetailsForm
            action="/horoscope"
            submitLabel="월운 다시 보기"
            secondarySubmitAction="/chart"
            secondarySubmitLabel="차트 근거 보기"
            showYearField
            defaultYear={selectedYear}
          />
        </section>
      </div>
    );
  }

  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">점성술로 보는 나만의 월운</span>
        <h1>이번 달의 흐름을 먼저 읽고, 오늘의 선택으로 이어가세요.</h1>
        <p className="muted hero-copy">
          출생 차트를 기준으로 이번 달의 핵심, 좋은 날짜와 주의 날짜, 분야별 상세를 먼저 보여줍니다.
          12개월 흐름과 차트 근거는 월운을 더 잘 이해하기 위한 보조 정보로 이어집니다.
        </p>
      </section>

      <section className="card" id="birth-details">
        <div className="section-heading">
          <div>
            <h2>나만의 월운을 볼 출생 정보 입력</h2>
            <p className="muted">
              생년월일, 시간, 도시와 조회 연도를 입력하면 바로 결과 중심 화면으로 전환됩니다.
            </p>
          </div>
        </div>

        <BirthDetailsForm
          action="/horoscope"
          submitLabel="나만의 월운 보기"
          secondarySubmitAction="/chart"
          secondarySubmitLabel="차트 근거 보기"
          showYearField
          defaultYear={selectedYear}
        />
      </section>

      <section className="card info-card">
        <h2>무엇을 먼저 보여주나요?</h2>
        <p>
          첫 화면은 이번 달 월운 요약, 좋은 날짜와 주의 날짜, 바로 이어갈 오늘 브리핑과 코치 동선입니다.
          연간 흐름은 아래에서 비교할 수 있습니다.
        </p>
      </section>
    </div>
  );
}
