"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { Route } from "next";
import {
  FloatingMenuItem,
  buildStoredBirthDetailsHref
} from "@/app/lib/floatingMenu";
import { readLastViewedBirthDetails } from "@/app/lib/birthDetailsStorage";

interface FloatingMenuProps {
  items: FloatingMenuItem[];
  copyText?: string;
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

export default function FloatingMenu({ items, copyText = "" }: FloatingMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const [recentHref, setRecentHref] = useState<Route | null>(null);

  useEffect(() => {
    const stored = readLastViewedBirthDetails(window.localStorage);

    if (stored) {
      setRecentHref(buildStoredBirthDetailsHref(stored, "chart"));
    }
  }, []);

  async function handleCopy() {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(copyText);
      } else if (!fallbackCopy(copyText)) {
        throw new Error("Clipboard fallback failed");
      }

      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1800);
    } catch {
      setCopyState("error");
      window.setTimeout(() => setCopyState("idle"), 2200);
    }
  }

  function handleTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
    setIsOpen(false);
  }

  function handleItemClick(item: FloatingMenuItem) {
    if (item.action === "copy") {
      void handleCopy();
      return;
    }

    if (item.action === "top") {
      handleTop();
      return;
    }

    setIsOpen(false);
  }

  const visibleItems = items.filter((item) => item.action !== "recent" || recentHref);

  return (
    <nav className="floating-menu" aria-label="빠른 메뉴">
      {isOpen ? (
        <div id="floating-menu-panel" className="floating-menu-panel open">
          {visibleItems.map((item) => {
            const label =
              item.action === "copy" && copyState === "copied"
                ? "복사 완료"
                : item.action === "copy" && copyState === "error"
                  ? "복사 실패"
                  : item.label;
            const href = item.action === "recent" ? recentHref : item.href;

            if (href) {
              return (
                <Link
                  key={`${item.label}-${href}`}
                  className="floating-menu-item"
                  href={href}
                  onClick={() => handleItemClick(item)}
                >
                  {label}
                </Link>
              );
            }

            return (
              <button
                key={item.label}
                className="floating-menu-item"
                type="button"
                onClick={() => handleItemClick(item)}
              >
                {label}
              </button>
            );
          })}
        </div>
      ) : null}

      <button
        className="floating-menu-toggle"
        type="button"
        aria-expanded={isOpen}
        aria-controls="floating-menu-panel"
        onClick={() => setIsOpen((current) => !current)}
      >
        {isOpen ? "닫기" : "메뉴"}
      </button>
    </nav>
  );
}
