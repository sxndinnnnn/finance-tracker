import type { Metadata, Viewport } from "next";
import "../styles/globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import { InstallPwaPrompt } from "@/components/InstallPwaPrompt";

export const metadata: Metadata = {
  title: "Finance Tracker",
  description: "Track income, expenses, loans, cards, and subscriptions — in your own currency.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Finance Tracker",
  },
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: "/icons/icon-192.png",
  },
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
        <InstallPwaPrompt />
      </body>
    </html>
  );
}
