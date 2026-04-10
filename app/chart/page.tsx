interface ChartPageProps {
  searchParams: {
    birthDate?: string;
    birthTime?: string;
    location?: string;
  };
}

export default function ChartPage({ searchParams }: ChartPageProps) {
  return (
    <div className="stack">
      <section className="card">
        <h1>Natal Chart</h1>
        <p className="muted">Chart rendering placeholder with captured birth data.</p>
      </section>

      <section className="card">
        <div className="details-grid">
          <p>
            <strong>Date:</strong> {searchParams.birthDate ?? "Not provided"}
          </p>
          <p>
            <strong>Time:</strong> {searchParams.birthTime ?? "Not provided"}
          </p>
          <p>
            <strong>Location:</strong> {searchParams.location ?? "Not provided"}
          </p>
        </div>
      </section>

      <section className="card chart-placeholder">
        <div className="orbital-ring">
          <span>☉</span>
        </div>
      </section>
    </div>
  );
}
