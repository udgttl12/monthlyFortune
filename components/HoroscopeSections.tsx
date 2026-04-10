interface HoroscopeData {
  career?: string;
  money?: string;
  love?: string;
  risk?: string;
}

async function getMonthlyHoroscope(): Promise<HoroscopeData> {
  const response = await fetch("http://localhost:8000/api/horoscope/monthly", {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to fetch horoscope");
  }

  return response.json();
}

function SectionCard({ title, content }: { title: string; content?: string }) {
  return (
    <article className="card section-card">
      <h2>{title}</h2>
      <p>{content ?? "No insight available yet."}</p>
    </article>
  );
}

export default async function HoroscopeSections() {
  const data = await getMonthlyHoroscope();

  return (
    <div className="section-grid">
      <SectionCard title="Career" content={data.career} />
      <SectionCard title="Money" content={data.money} />
      <SectionCard title="Love" content={data.love} />
      <SectionCard title="Risk" content={data.risk} />
    </div>
  );
}
