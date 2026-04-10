import Link from "next/link";

export default function HomePage() {
  return (
    <div className="stack">
      <section className="card hero-card">
        <h1>Monthly Fortune</h1>
        <p className="muted">Generate your personalized astrology chart and monthly outlook.</p>
      </section>

      <section className="card">
        <h2>Birth Details</h2>
        <form className="form-grid" action="/chart" method="GET">
          <label>
            Birth date
            <input type="date" name="birthDate" required />
          </label>

          <label>
            Birth time
            <input type="time" name="birthTime" required />
          </label>

          <label className="full-width">
            Birth location
            <input type="text" name="location" placeholder="City, Country" required />
          </label>

          <div className="button-row full-width">
            <button type="submit">View Natal Chart</button>
            <Link className="btn-secondary" href="/horoscope">
              Read Monthly Horoscope
            </Link>
          </div>
        </form>
      </section>
    </div>
  );
}
