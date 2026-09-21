"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useAuth } from "@/hooks/useAuth";
import { useCurrencies } from "@/hooks/useCurrencies";
import { api, ApiError } from "@/lib/api-client";
import type { User } from "@/types";

interface FormValues {
  full_name: string;
  base_currency_code: string;
  locale: string;
  timezone: string;
  default_reminder_days_before: number;
}

export default function Page() {
  const { user, refreshUser } = useAuth();
  const { currencies } = useCurrencies();
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, isDirty },
  } = useForm<FormValues>();

  useEffect(() => {
    if (user) {
      reset({
        full_name: user.full_name,
        base_currency_code: user.base_currency_code,
        locale: user.locale,
        timezone: user.timezone,
        default_reminder_days_before: user.default_reminder_days_before,
      });
    }
  }, [user, reset]);

  async function onSubmit(values: FormValues) {
    setServerError(null);
    setSaved(false);
    try {
      const updated = await api.patch<User>("/auth/me", values);
      await refreshUser();
      reset({
        full_name: updated.full_name,
        base_currency_code: updated.base_currency_code,
        locale: updated.locale,
        timezone: updated.timezone,
        default_reminder_days_before: updated.default_reminder_days_before,
      });
      setSaved(true);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong");
    }
  }

  if (!user) return null;

  return (
    <main className="max-w-lg">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Settings</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        These drive currency conversion and formatting throughout the app.
      </p>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mt-6 space-y-4 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
      >
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Full name</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            {...register("full_name", { required: true })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Email</label>
          <input
            disabled
            value={user.email}
            className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-400 dark:border-slate-800 dark:bg-slate-950"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Base currency</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            {...register("base_currency_code")}
          >
            {currencies.map((c) => (
              <option key={c.code} value={c.code}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-slate-400">Used to convert your dashboard totals.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Locale</label>
          <input
            placeholder="en-US"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            {...register("locale", { required: true })}
          />
          <p className="mt-1 text-xs text-slate-400">BCP-47 code — drives number and date formatting.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Timezone</label>
          <input
            placeholder="Asia/Colombo"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            {...register("timezone", { required: true })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Default reminder lead time (days)
          </label>
          <input
            type="number"
            min={0}
            max={365}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            {...register("default_reminder_days_before", { valueAsNumber: true, min: 0, max: 365 })}
          />
          <p className="mt-1 text-xs text-slate-400">
            Applies to any subscription without its own reminder setting.
          </p>
        </div>

        {serverError && <p className="text-sm text-red-600">{serverError}</p>}
        {saved && !isDirty && <p className="text-sm text-emerald-600">Saved.</p>}

        <button
          type="submit"
          disabled={isSubmitting || !isDirty}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900"
        >
          {isSubmitting ? "Saving…" : "Save changes"}
        </button>
      </form>
    </main>
  );
}
