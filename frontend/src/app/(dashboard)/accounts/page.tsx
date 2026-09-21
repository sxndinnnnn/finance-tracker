"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useResource } from "@/hooks/useResource";
import { useCurrencies } from "@/hooks/useCurrencies";
import { useAuth } from "@/hooks/useAuth";
import { Money } from "@/components/Money";
import { ApiError } from "@/lib/api-client";
import type { Account, AccountType } from "@/types";

const ACCOUNT_TYPES: { value: AccountType; label: string }[] = [
  { value: "bank", label: "Bank" },
  { value: "cash", label: "Cash" },
  { value: "wallet", label: "Wallet" },
];

interface FormValues {
  name: string;
  type: AccountType;
  currency_code: string;
  opening_balance_major: number;
}

export default function Page() {
  const { user } = useAuth();
  const { items: accounts, loading, create, remove } = useResource<Account>("/accounts");
  const { currencies } = useCurrencies();
  const [showForm, setShowForm] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: { currency_code: user?.base_currency_code, opening_balance_major: 0 },
  });

  const selectedCurrency = currencies.find((c) => c.code === watch("currency_code"));
  const decimalPlaces = selectedCurrency?.decimal_places ?? 2;

  async function onSubmit(values: FormValues) {
    setServerError(null);
    try {
      await create({
        name: values.name,
        type: values.type,
        currency_code: values.currency_code,
        opening_balance_minor: Math.round(values.opening_balance_major * 10 ** decimalPlaces),
      });
      reset({ currency_code: user?.base_currency_code, opening_balance_major: 0, name: "" });
      setShowForm(false);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong");
    }
  }

  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Accounts</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          {showForm ? "Cancel" : "New account"}
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
              {...register("name", { required: "Name is required" })}
            />
            {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Type</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("type")}
            >
              {ACCOUNT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Currency</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("currency_code")}
            >
              {currencies.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Opening balance
            </label>
            <input
              type="number"
              step={1 / 10 ** decimalPlaces}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("opening_balance_major", { valueAsNumber: true })}
            />
          </div>
          {serverError && <p className="sm:col-span-2 text-sm text-red-600">{serverError}</p>}
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900"
            >
              {isSubmitting ? "Saving…" : "Create account"}
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 space-y-2">
        {loading && <p className="text-sm text-slate-400">Loading…</p>}
        {!loading && accounts.length === 0 && (
          <p className="text-sm text-slate-400">No accounts yet — add your first one above.</p>
        )}
        {accounts.map((account) => (
          <div
            key={account.id}
            className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
          >
            <div>
              <p className="font-medium text-slate-900 dark:text-slate-50">{account.name}</p>
              <p className="text-xs uppercase tracking-wide text-slate-400">
                {account.type} · {account.currency_code}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="font-mono text-sm text-slate-900 dark:text-slate-100">
                <Money amountMinor={account.current_balance_minor} currencyCode={account.currency_code} />
              </span>
              <button
                onClick={() => remove(account.id)}
                className="text-xs text-red-600 hover:underline"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
