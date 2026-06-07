import BirthDetailsForm from "@/components/BirthDetailsForm";
import FloatingMenu from "@/components/FloatingMenu";
import HomeResumePanel from "@/components/HomeResumePanel";
import YongyongMascot from "@/components/YongyongMascot";
import { buildFloatingMenuItems } from "@/app/lib/floatingMenu";

export default function HomePage() {
  return (
    <div className="stack">
      <section className="card hero-card home-hero">
        <div className="home-hero-copy">
          <span className="eyebrow">용용이와 함께 보는 월간 별자리 흐름</span>
          <h1>점성술로 보는 나만의 월운</h1>
          <p className="muted hero-copy">
            출생 정보로 내 차트의 기준점을 잡고, 이번 달에 강해지는 흐름과 조심할 날짜를 먼저 읽어보세요.
            차트는 근거가 되고, 월운은 이번 달의 선택을 도와주는 메인 리포트입니다.
          </p>
          <div className="pill-row">
            <span className="info-pill">이번 달 핵심 요약</span>
            <span className="info-pill">좋은 날짜 / 주의 날짜</span>
            <span className="info-pill">오늘 브리핑과 코치로 이어보기</span>
          </div>
        </div>
        <YongyongMascot variant="hero" caption="수정구슬에 이번 달의 리듬을 비춰볼게요." />
      </section>

      <HomeResumePanel />

      <section className="card birth-entry-card" id="birth-details">
        <div className="section-heading">
          <div>
            <span className="eyebrow">나만의 월운 보기</span>
            <h2>출생 정보를 입력하면 바로 이번 달 월운으로 이동합니다</h2>
            <p className="muted">
              생년월일, 시간, 도시만 입력하면 월운 리포트를 먼저 보여주고, 차트 근거는 필요할 때 확인할 수 있습니다.
            </p>
          </div>
        </div>

        <BirthDetailsForm
          action="/horoscope"
          submitLabel="나만의 월운 보기"
          secondarySubmitAction="/chart"
          secondarySubmitLabel="출생 차트로 근거 보기"
        />
      </section>

      <section className="info-grid">
        <article className="card info-card">
          <h2>월운이 먼저입니다</h2>
          <p>
            첫 결과는 이번 달의 핵심, 좋은 날짜, 주의 날짜, 분야별 상세입니다. 12개월 흐름과 차트는 월운을
            더 잘 이해하기 위한 보조 정보로 배치합니다.
          </p>
        </article>

        <article className="card info-card">
          <h2>DB 없이도 시작할 수 있어요</h2>
          <p>
            최근 입력은 브라우저에 가볍게 저장합니다. 계정과 서버 저장함은 나중에 붙이더라도, 핵심 월운 경험은
            지금 바로 자연스럽게 사용할 수 있어야 합니다.
          </p>
        </article>
      </section>

      <FloatingMenu items={buildFloatingMenuItems({ page: "home" })} />
    </div>
  );
}
