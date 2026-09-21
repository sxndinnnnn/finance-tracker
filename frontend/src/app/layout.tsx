import type { Metadata, Viewport } from "next";
import "../styles/globals.css";
import { AuthProvider } from "@/components/AuthProvider";

export const metadata: Metadata = {
  title: "Finance Tracker",
  description: "Track income, expenses, loans, cards, and subscriptions — in your own currency.",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // lang is left generic here — the signed-in user's own locale drives
  // number/date formatting throughout the app instead (see lib/currency.ts).
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
