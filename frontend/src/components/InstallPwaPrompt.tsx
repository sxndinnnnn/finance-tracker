"use client";

import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const DISMISSED_KEY = "finance_tracker_pwa_prompt_dismissed";

export function InstallPwaPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Registration failure shouldn't block the app — PWA install is a bonus, not a requirement.
      });
    }

    function onBeforeInstallPrompt(event: Event) {
      event.preventDefault();
      let dismissed = false;
      try {
        dismissed = window.localStorage.getItem(DISMISSED_KEY) === "1";
      } catch {
        // localStorage unavailable (private mode, blocked) — just show the prompt.
      }
      if (dismissed) return;
      setDeferredPrompt(event as BeforeInstallPromptEvent);
      setVisible(true);
    }

    window.addEventListener("beforeinstallprompt", onBeforeInstallPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onBeforeInstallPrompt);
  }, []);

  if (!visible || !deferredPrompt) return null;

  async function install() {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setVisible(false);
    setDeferredPrompt(null);
  }

  function dismiss() {
    setVisible(false);
    try {
      window.localStorage.setItem(DISMISSED_KEY, "1");
    } catch {
      // best-effort only
    }
  }

  return (
    <div className="fixed inset-x-4 bottom-4 z-50 flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-lg sm:left-auto sm:right-4 sm:w-80 dark:border-slate-700 dark:bg-slate-900">
      <p className="text-sm text-slate-700 dark:text-slate-300">Install Finance Tracker for quick access.</p>
      <div className="flex shrink-0 gap-2">
        <button onClick={dismiss} className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
          Not now
        </button>
        <button
          onClick={install}
          className="rounded-md bg-slate-900 px-2.5 py-1 text-xs font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          Install
        </button>
      </div>
    </div>
  );
}
