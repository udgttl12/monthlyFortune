import AuthForm from "@/components/AuthForm";

export default function SignupPage() {
  return (
    <div className="stack">
      <section className="card hero-card">
        <span className="eyebrow">회원가입</span>
        <h1>운세 결과를 다시 계산하지 않도록 계정을 준비합니다.</h1>
        <p className="muted hero-copy">
          v1에서는 이메일 계정을 만들고 로그인 상태를 유지합니다. 운세 결과는 MariaDB 캐시에 저장되어
          같은 조건의 조회가 반복될 때 API 비용을 줄입니다.
        </p>
      </section>
      <section className="card">
        <AuthForm mode="signup" />
      </section>
    </div>
  );
}
