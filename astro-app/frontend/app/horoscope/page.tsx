"use client";

import { useMemo, useState } from "react";
import { BirthForm } from "@/components/BirthForm";
import { fetchMonthlyHoroscope } from "@/services/api";

export default function HoroscopePage() {
  const today = useMemo(() => new Date(), []);
  const [status, setStatus] = useState("");
  const [data, setData] = useState<any>(null);

  const submit = async (payload: Record<string, string>) => {
    setStatus("Analyzing planets...");
    const result = await fetchMonthlyHoroscope(
      payload as any,
      String(today.getFullYear()),
      String(today.getMonth() + 1),
    );
    setData(result);
    setStatus("");
  };

  return (
    <main>
      <h1>Monthly Horoscope</h1>
      <BirthForm onSubmit={submit} buttonLabel="Get Monthly Horoscope" />
      {status && <p className="status">{status}</p>}
      {data && (
        <>
          <h2>Cards</h2>
          <div className="card-grid">
            {Object.entries(data.cards).map(([key, value]) => (
              <div className="card" key={key}>
                <h3 style={{ textTransform: "capitalize" }}>{key}</h3>
                <p>{String(value)}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  );
}
