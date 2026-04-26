import BirthDetailsForm from "@/components/BirthDetailsForm";

export default function HomePage() {
  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">개인 맞춤 점성술 리딩</span>
        <h1>출생 정보로 차트와 연간 운세를 함께 읽어보세요.</h1>
        <p className="muted hero-copy">
          Monthly Fortune은 출생 일시와 도시를 기준으로 네이탈 차트를 계산하고, 그 위에 월별 흐름을 덧입혀
          연간 개요와 월 상세 운세를 보여줍니다. 차트 확인과 운세 조회를 같은 폼에서 바로 시작할 수 있습니다.
        </p>
        <div className="pill-row">
          <span className="info-pill">출생 차트 계산</span>
          <span className="info-pill">연간 개요 + 월 상세</span>
          <span className="info-pill">좋은 날짜 / 주의 날짜</span>
        </div>
      </section>

      <section className="card">
        <div className="section-heading">
          <div>
            <h2>출생 정보 입력</h2>
            <p className="muted">
              먼저 기본 정보를 입력하면 출생 차트와 개인 맞춤 운세를 바로 확인할 수 있습니다.
            </p>
          </div>
        </div>

        <BirthDetailsForm
          action="/chart"
          submitLabel="출생 차트 보기"
          secondarySubmitAction="/horoscope"
          secondarySubmitLabel="개인 운세 보기"
        />
      </section>

      <section className="info-grid">
        <article className="card info-card">
          <h2>무엇을 볼 수 있나요?</h2>
          <p>
            태양, 달, 주요 행성, ASC, MC, Whole Sign House를 계산하고 그 결과를 바탕으로 올해 12개월의 흐름과
            선택한 달의 상세 리딩을 제공합니다.
          </p>
        </article>

        <article className="card info-card">
          <h2>운세는 어떻게 만들어지나요?</h2>
          <p>
            백엔드에서 점성 계산을 먼저 수행하고, 월 상세 리딩은 구조화된 결과를 바탕으로 자연어 분석을
            확장합니다. API가 없더라도 기본 해석은 계속 제공됩니다.
          </p>
        </article>
      </section>
    </div>
  );
}
