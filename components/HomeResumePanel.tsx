"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { readLastViewedBirthDetails } from "@/app/lib/birthDetailsStorage";
import {
  buildMonthlyResumeLinks,
  formatBirthProfileSummary,
  type MonthlyResumeLink
} from "@/app/lib/experienceContext";

type ResumeState = {
  readonly profileSummary: string;
  readonly links: readonly MonthlyResumeLink[];
};

export default function HomeResumePanel() {
  const [resumeState, setResumeState] = useState<ResumeState | null>(null);

  useEffect(() => {
    const storedDetails = readLastViewedBirthDetails(window.localStorage);

    if (!storedDetails) {
      return;
    }

    setResumeState({
      profileSummary: formatBirthProfileSummary(storedDetails),
      links: buildMonthlyResumeLinks(storedDetails)
    });
  }, []);

  if (!resumeState) {
    return null;
  }

  return (
    <section className="card resume-panel" aria-label="최근 월운 이어보기">
      <div className="section-heading">
        <div>
          <span className="eyebrow">최근 월운 이어보기</span>
          <h2>지난 입력으로 바로 이어서 볼까요?</h2>
          <p className="muted">{resumeState.profileSummary}</p>
        </div>
      </div>

      <div className="resume-link-grid">
        {resumeState.links.map((link) => (
          <Link key={link.kind} className={`resume-link ${link.kind}`} href={link.href}>
            <strong>{link.label}</strong>
            <span>{link.description}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
