import AccountPanel from "@/components/AccountPanel";

export default function AccountPage() {
  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">계정</span>
        <h1>내 저장 공간</h1>
        <p className="muted hero-copy">
          지금은 로그인 상태 확인을 제공하고, 다음 단계에서 저장한 출생 정보와 운세 기록을 이곳에 연결합니다.
        </p>
      </section>
      <AccountPanel />
    </div>
  );
}
