"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_MONTHLY_FORTUNE_API_URL ?? "";

export default function AccountPanel() {
  const [email, setEmail] = useState<string | null>(null);
  const [message, setMessage] = useState("로그인 상태를 확인하는 중입니다.");

  useEffect(() => {
    const token = localStorage.getItem("monthly_fortune_auth_token");
    const storedEmail = localStorage.getItem("monthly_fortune_auth_email");

    if (!token) {
      setMessage("아직 로그인하지 않았습니다.");
      return;
    }

    if (storedEmail) {
      setEmail(storedEmail);
    }

    fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.detail ?? "로그인이 만료되었습니다.");
        }
        localStorage.setItem("monthly_fortune_auth_email", payload.email);
        setEmail(payload.email);
        setMessage("로그인되어 있습니다.");
      })
      .catch((error) => {
        setEmail(null);
        setMessage(error instanceof Error ? error.message : "로그인 상태를 확인하지 못했습니다.");
      });
  }, []);

  function logout() {
    localStorage.removeItem("monthly_fortune_auth_token");
    localStorage.removeItem("monthly_fortune_auth_email");
    setEmail(null);
    setMessage("로그아웃되었습니다.");
  }

  return (
    <section className="card account-panel">
      <h2>내 계정</h2>
      <p className="muted">{message}</p>
      {email ? <p className="account-email">{email}</p> : null}
      <div className="button-row">
        {email ? (
          <button type="button" onClick={logout}>
            로그아웃
          </button>
        ) : (
          <>
            <Link className="button-link" href="/login">
              로그인
            </Link>
            <Link className="button-link" href="/signup">
              회원가입
            </Link>
          </>
        )}
      </div>
    </section>
  );
}
