"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useResource } from "@/hooks/useResource";
import { useCurrencies } from "@/hooks/useCurrencies";
import { useAuth } from "@/hooks/useAuth";
import { Money } from "@/components/Money";
import { formatDate } from "@/lib/currency";
import { ApiError } from "@/lib/api-client";
import type { Account, InterestType, Loan } from "@/types";

interface FormValues {
  name: string;
  lender: string;
  principal_major: number;
  currency_code: string;
  interest_rate: number;
  interest_type: InterestType;
  term_months: number;
  start_date: string;
  payment_amount_major: number;
  linked_account_id: string;
}

export default function Page() {
  const { user } = useAuth();
  const { items: accounts } = useResource<Account>("/accounts");
  const { items: loans, loading, create, remove } = useResource<Loan>("/loans");
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
    defaultValues: {
      currency_code: user?.base_currency_code,
      interest_type: "fixed",
      start_date: new Date().toISOString().slice(0, 10),
    },
  });

  const decimalPlaces = currencies.find((c) => c.code === watch("currency_code"))?.decimal_places ?? 2;

  async function onSubmit(values: FormValues) {
    setServerError(null);
    try {
      await create({
        name: values.name,
        lender: values.lender,
        principal_minor: Math.round(values.principal_major * 10 ** decimalPlaces),
        currency_code: values.currency_code,
        interest_rate: values.interest_rate,
        interest_type: values.interest_type,
        term_months: values.term_months,
        start_date: values.start_date,
        payment_amount_minor: Math.round(values.payment_amount_major * 10 ** decimalPlaces),
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
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Loans</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          {showForm ? "Cancel" : "New loan"}
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
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Lender</label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("lender", { required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Principal</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("principal_major", { valueAsNumber: true, required: true })}
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
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Interest rate (%)
            </label>
            <input
              type="number"
              step="0.01"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("interest_rate", { valueAsNumber: true, required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Interest type</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("interest_type")}
            >
              <option value="fixed">Fixed</option>
              <option value="variable">Variable</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Term (months)</label>
            <input
              type="number"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("term_months", { valueAsNumber: true, required: true })}
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
              {...register("payment_amount_major", { valueAsNumber: true, required: true })}
            />
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
              Repayment account
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
              {isSubmitting ? "Saving…" : "Create loan"}
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 space-y-2">
        {loading && <p className="text-sm text-slate-400">Loading…</p>}
        {!loading && loans.length === 0 && <p className="text-sm text-slate-400">No loans yet.</p>}
        {loans.map((loan) => {
          const progress = 1 - loan.remaining_balance_minor / loan.principal_minor;
          return (
            <div
              key={loan.id}
              className="rounded-lg border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-50">{loan.name}</p>
                  <p className="text-xs text-slate-400">
                    {loan.lender} · {loan.interest_rate}% {loan.interest_type} · started{" "}
                    {formatDate(loan.start_date, user?.locale)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="font-mono text-sm text-slate-900 dark:text-slate-100">
                      <Money amountMinor={loan.remaining_balance_minor} currencyCode={loan.currency_code} />{" "}
                      remaining
                    </p>
                    <p className="text-xs text-slate-400">
                      of <Money amountMinor={loan.principal_minor} currencyCode={loan.currency_code} />
                    </p>
                  </div>
                  <button onClick={() => remove(loan.id)} className="text-xs text-red-600 hover:underline">
                    Delete
                  </button>
                </div>
              </div>
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full rounded-full bg-slate-900 dark:bg-slate-100"
                  style={{ width: `${Math.min(Math.max(progress * 100, 0), 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </main>
  );
}
