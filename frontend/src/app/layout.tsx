import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Finance Tracker",
  description: "Track income, expenses, loans, cards, and subscriptions — in your own currency.",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // lang is left generic here — drive it from the signed-in user's locale
  // once auth exists, rather than hardcoding "en".
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
