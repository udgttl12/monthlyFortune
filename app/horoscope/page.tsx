import { Suspense } from "react";
import HoroscopeSections from "@/components/HoroscopeSections";
import Spinner from "@/components/Spinner";

export const dynamic = "force-dynamic";

export default function HoroscopePage() {
  return (
    <div className="stack">
      <section className="card">
        <h1>Monthly Horoscope</h1>
        <p className="muted">Live feed from your astrology backend with progressive rendering.</p>
      </section>

      <Suspense fallback={<Spinner />}>
        <HoroscopeSections />
      </Suspense>
    </div>
  );
}
