import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">로그인</span>
        <h1>이전에 만든 계정으로 들어오세요.</h1>
        <p className="muted hero-copy">
          로그인 기능은 저장된 결과와 사용자별 기록을 연결하기 위한 기반입니다.
        </p>
      </section>
      <section className="card">
        <AuthForm mode="login" />
      </section>
    </div>
  );
}
