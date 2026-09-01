import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIH26190 — Secure Document Management System",
  description:
    "Secure Case, Evidence & Legal Document Management System (Smart India Hackathon 2026 prototype)",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
