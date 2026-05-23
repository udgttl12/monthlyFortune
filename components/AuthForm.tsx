"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_MONTHLY_FORTUNE_API_URL ?? "";

interface AuthFormProps {
  mode: "signup" | "login";
}

export default function AuthForm({ mode }: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(payload.detail ?? "요청을 처리하지 못했습니다.");
      }

      localStorage.setItem("monthly_fortune_auth_token", payload.token);
      localStorage.setItem("monthly_fortune_auth_email", payload.email);
      setStatus("done");
      setMessage(mode === "signup" ? "회원가입이 완료되었습니다." : "로그인되었습니다.");
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "요청을 처리하지 못했습니다.");
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label>
        이메일
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          required
        />
      </label>
      <label>
        비밀번호
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete={mode === "signup" ? "new-password" : "current-password"}
          minLength={8}
          required
        />
      </label>
      <button type="submit" disabled={status === "loading"}>
        {status === "loading" ? "처리 중..." : mode === "signup" ? "회원가입" : "로그인"}
      </button>
      {message ? <p className={status === "error" ? "form-error" : "auth-success"}>{message}</p> : null}
      {status === "done" ? (
        <Link className="button-link" href="/account">
          내 계정 보기
        </Link>
      ) : null}
    </form>
  );
}
