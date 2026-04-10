import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>Astrology SaaS</h1>
      <p>Generate your natal chart and monthly horoscope from one workspace.</p>
      <div className="card-grid">
        <div className="card">
          <h3>Chart</h3>
          <p>Calculate planets, houses, and aspects from birth data.</p>
          <Link href="/chart">Go to Chart</Link>
        </div>
        <div className="card">
          <h3>Monthly Horoscope</h3>
          <p>Review career, money, love, and risk cards for the month.</p>
          <Link href="/horoscope">Go to Horoscope</Link>
        </div>
      </div>
    </main>
  );
}
