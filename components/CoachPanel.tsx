"use client";

import { FormEvent, useState } from "react";
import type { CoachResponse } from "@/app/lib/aiRetention";
import { appendAiRetentionArchiveItem } from "@/app/lib/aiRetentionStorage";
import type { HoroscopeSearchParams } from "@/app/lib/horoscope";

const API_BASE_URL = process.env.NEXT_PUBLIC_MONTHLY_FORTUNE_API_URL ?? "";

interface CoachPanelProps {
  searchParams: HoroscopeSearchParams;
  year: number;
  month: number;
}

export default function CoachPanel({ searchParams, year, month }: CoachPanelProps) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<CoachResponse | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (question.trim().length < 4) {
      setStatus("error");
      return;
    }

    setStatus("loading");
    setResponse(null);

    try {
      const result = await fetch(`${API_BASE_URL}/api/ai-retention/coach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          birthDate: searchParams.birthDate,
          birthTime: searchParams.birthTime,
          city: searchParams.city,
          countryCode: searchParams.country,
          timezone: searchParams.timezone,
          year,
          month,
          question
        })
      });

      if (!result.ok) {
        setStatus("error");
        return;
      }

      const payload: CoachResponse = await result.json();
      setResponse(payload);
      setStatus("idle");
      appendAiRetentionArchiveItem(window.localStorage, {
        id: crypto.randomUUID(),
        type: "coach",
        title: payload.question,
        createdAt: new Date().toISOString(),
        payload
      });
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="stack">
      <form className="card coach-form" onSubmit={submitQuestion}>
        <label htmlFor="coach-question">
          무엇을 결정하고 싶나요?
          <textarea
            id="coach-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="예: 다음 주 면접 준비는 언제 집중하는 게 좋을까?"
            rows={5}
          />
        </label>
        <button type="submit" disabled={status === "loading"}>
          {status === "loading" ? "분석 중" : "AI 코치에게 묻기"}
        </button>
        {status === "error" ? <p className="form-error">질문을 확인하고 다시 시도해 주세요.</p> : null}
      </form>

      {response ? (
        <section className="card coach-answer">
          <div className="section-heading">
            <div>
              <h2>AI 코치 답변</h2>
              <p className="muted">{response.reasoningSummary}</p>
            </div>
            <span className={`query-pill ${response.llmEnhanced ? "active" : ""}`}>
              {response.llmEnhanced ? "AI 코치" : "기본 코치"}
            </span>
          </div>
          <p>{response.answer}</p>
          <div className="section-grid two-column-grid">
            <article className="section-card">
              <h3>추천 날짜</h3>
              {response.recommendedDates.map((item) => (
                <p key={`${item.date}-${item.label}`}>
                  <strong>{item.date}</strong> {item.label}: {item.reason}
                </p>
              ))}
            </article>
            <article className="section-card">
              <h3>주의 날짜</h3>
              {response.cautionDates.map((item) => (
                <p key={`${item.date}-${item.label}`}>
                  <strong>{item.date}</strong> {item.label}: {item.reason}
                </p>
              ))}
            </article>
          </div>
          <article className="section-card">
            <h3>첫 행동</h3>
            <p>{response.firstAction}</p>
          </article>
          <article className="section-card">
            <h3>메시지 초안</h3>
            <p>{response.messageDraft}</p>
          </article>
          <p className="muted">{response.disclaimer}</p>
        </section>
      ) : null}
    </div>
  );
}
