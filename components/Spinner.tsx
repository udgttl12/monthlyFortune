export default function Spinner() {
  return (
    <div className="spinner-wrap" role="status" aria-label="Loading">
      <div className="spinner" />
      <p className="muted">별의 흐름을 읽는 중입니다...</p>
    </div>
  );
}
