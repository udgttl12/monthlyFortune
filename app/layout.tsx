import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Monthly Fortune",
  description: "출생 차트와 개인 맞춤 연간/월간 운세를 함께 보는 점성술 앱"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <main className="shell">{children}</main>
      </body>
    </html>
  );
}
