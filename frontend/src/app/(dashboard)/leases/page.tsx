"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useResource } from "@/hooks/useResource";
import { useCurrencies } from "@/hooks/useCurrencies";
import { useAuth } from "@/hooks/useAuth";
import { Money } from "@/components/Money";
import { formatDate } from "@/lib/currency";
import { ApiError } from "@/lib/api-client";
import type { Account, Lease } from "@/types";

interface FormValues {
  name: string;
  asset_description: string;
  lessor: string;
  monthly_payment_major: number;
  currency_code: string;
  start_date: string;
  end_date: string;
  linked_account_id: string;
}

export default function Page() {
  const { user } = useAuth();
  const { items: accounts } = useResource<Account>("/accounts");
  const { items: leases, loading, create, remove } = useResource<Lease>("/leases");
  const { currencies } = useCurrencies();
  const [showForm, setShowForm] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { isSubmitting },
  } = useForm<FormValues>({
    defaultValues: {
      currency_code: user?.base_currency_code,
      start_date: new Date().toISOString().slice(0, 10),
    },
  });

  const decimalPlaces = currencies.find((c) => c.code === watch("currency_code"))?.decimal_places ?? 2;

  async function onSubmit(values: FormValues) {
    setServerError(null);
    try {
      await create({
        name: values.name,
        asset_description: values.asset_description || undefined,
        lessor: values.lessor,
        monthly_payment_minor: Math.round(values.monthly_payment_major * 10 ** decimalPlaces),
        currency_code: values.currency_code,
        start_date: values.start_date,
        end_date: values.end_date || undefined,
        linked_account_id: values.linked_account_id,
        recurrence: { frequency: "monthly", interval: 1, start_date: values.start_date },
      });
      reset();
      setShowForm(false);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong");
    }
  }

  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Leases</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          {showForm ? "Cancel" : "New lease"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-4 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2 dark:border-slate-800 dark:bg-slate-900"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Name</label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("name", { required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Lessor</label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("lessor", { required: true })}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Asset description (optional)
            </label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("asset_description")}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Monthly payment
            </label>
            <input
              type="number"
              step="0.01"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("monthly_payment_major", { valueAsNumber: true, required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Currency</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("currency_code")}
            >
              {currencies.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Start date</label>
            <input
              type="date"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("start_date", { required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              End date (optional)
            </label>
            <input
              type="date"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("end_date")}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Payment account
            </label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("linked_account_id", { required: true })}
            >
              <option value="">Select an account</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          {serverError && <p className="sm:col-span-2 text-sm text-red-600">{serverError}</p>}
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900"
            >
              {isSubmitting ? "Saving…" : "Create lease"}
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 space-y-2">
        {loading && <p className="text-sm text-slate-400">Loading…</p>}
        {!loading && leases.length === 0 && <p className="text-sm text-slate-400">No leases yet.</p>}
        {leases.map((lease) => (
          <div
            key={lease.id}
            className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
          >
            <div>
              <p className="font-medium text-slate-900 dark:text-slate-50">{lease.name}</p>
              <p className="text-xs text-slate-400">
                {lease.lessor}
                {lease.asset_description ? ` · ${lease.asset_description}` : ""} · from{" "}
                {formatDate(lease.start_date, user?.locale)}
                {lease.end_date ? ` to ${formatDate(lease.end_date, user?.locale)}` : ""}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="font-mono text-sm text-slate-900 dark:text-slate-100">
                <Money amountMinor={lease.monthly_payment_minor} currencyCode={lease.currency_code} />/mo
              </span>
              <button onClick={() => remove(lease.id)} className="text-xs text-red-600 hover:underline">
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
