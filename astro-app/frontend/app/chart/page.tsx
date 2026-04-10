"use client";

import { useState } from "react";
import { BirthForm } from "@/components/BirthForm";
import { fetchChart } from "@/services/api";

export default function ChartPage() {
  const [status, setStatus] = useState("");
  const [chart, setChart] = useState<any>(null);

  const submit = async (payload: Record<string, string>) => {
    setStatus("Calculating chart...");
    const data = await fetchChart(payload as any);
    setChart(data);
    setStatus("");
  };

  return (
    <main>
      <h1>Natal Chart</h1>
      <BirthForm onSubmit={submit} buttonLabel="Calculate Chart" />
      {status && <p className="status">{status}</p>}
      {chart && (
        <>
          <h2>Planets</h2>
          <div className="card-grid">
            {chart.planets.map((planet: any) => (
              <div className="card" key={planet.name}>
                <strong>{planet.name}</strong>
                <p>{planet.longitude}°</p>
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  );
}
