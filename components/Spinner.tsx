export default function Spinner() {
  return (
    <div className="spinner-wrap" role="status" aria-label="Loading">
      <div className="spinner" />
      <p className="muted">Reading the stars...</p>
    </div>
  );
}
