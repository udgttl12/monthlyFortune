"use client";

import { useState } from "react";

interface CopyResultsButtonProps {
  text: string;
  label?: string;
}

type CopyState = "idle" | "copied" | "error";

function fallbackCopy(text: string) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.top = "-9999px";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();

  try {
    return document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}

export default function CopyResultsButton({
  text,
  label = "ChatGPT용 전체 복사"
}: CopyResultsButtonProps) {
  const [copyState, setCopyState] = useState<CopyState>("idle");

  async function handleCopy() {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else if (!fallbackCopy(text)) {
        throw new Error("Clipboard fallback failed");
      }

      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1800);
    } catch {
      setCopyState("error");
      window.setTimeout(() => setCopyState("idle"), 2200);
    }
  }

  const buttonLabel =
    copyState === "copied" ? "복사 완료" : copyState === "error" ? "복사 실패" : label;

  return (
    <button className="copy-results-button" type="button" onClick={handleCopy}>
      {buttonLabel}
    </button>
  );
}
