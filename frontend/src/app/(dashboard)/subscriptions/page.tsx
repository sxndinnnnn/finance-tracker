"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useResource } from "@/hooks/useResource";
import { useCurrencies } from "@/hooks/useCurrencies";
import { useAuth } from "@/hooks/useAuth";
import { Money } from "@/components/Money";
import { formatDate } from "@/lib/currency";
import { ApiError } from "@/lib/api-client";
import type { Account, CreditCard, Subscription } from "@/types";

interface FormValues {
  name: string;
  amount_major: number;
  currency_code: string;
  next_billing_date: string;
  linked_credit_card_id: string;
  linked_account_id: string;
  reminder_days_before: number | "";
}

export default function Page() {
  const { user } = useAuth();
  const { items: cards } = useResource<CreditCard>("/credit-cards");
  const { items: accounts } = useResource<Account>("/accounts");
  const { items: subscriptions, loading, create, update, remove } = useResource<Subscription>("/subscriptions");
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
      next_billing_date: new Date().toISOString().slice(0, 10),
    },
  });

  const decimalPlaces = currencies.find((c) => c.code === watch("currency_code"))?.decimal_places ?? 2;

  async function onSubmit(values: FormValues) {
    setServerError(null);
    try {
      await create({
        name: values.name,
        amount_minor: Math.round(values.amount_major * 10 ** decimalPlaces),
        currency_code: values.currency_code,
        next_billing_date: values.next_billing_date,
        linked_credit_card_id: values.linked_credit_card_id || undefined,
        linked_account_id: values.linked_credit_card_id ? undefined : values.linked_account_id || undefined,
        reminder_days_before: values.reminder_days_before === "" ? undefined : values.reminder_days_before,
        recurrence: { frequency: "monthly", interval: 1, start_date: values.next_billing_date },
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
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Subscriptions</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          {showForm ? "Cancel" : "New subscription"}
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
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Amount</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("amount_major", { valueAsNumber: true, required: true })}
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
              Next billing date
            </label>
            <input
              type="date"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("next_billing_date", { required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Charged to card (optional)
            </label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("linked_credit_card_id")}
            >
              <option value="">None</option>
              {cards.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.card_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Or paid from account (optional)
            </label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              disabled={!!watch("linked_credit_card_id")}
              {...register("linked_account_id")}
            >
              <option value="">None</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Remind me N days before (optional — defaults to your account setting)
            </label>
            <input
              type="number"
              min={0}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("reminder_days_before", { valueAsNumber: true })}
            />
          </div>
          {serverError && <p className="sm:col-span-2 text-sm text-red-600">{serverError}</p>}
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900"
            >
              {isSubmitting ? "Saving…" : "Add subscription"}
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 space-y-2">
        {loading && <p className="text-sm text-slate-400">Loading…</p>}
        {!loading && subscriptions.length === 0 && (
          <p className="text-sm text-slate-400">No subscriptions yet.</p>
        )}
        {subscriptions.map((sub) => {
          const card = cards.find((c) => c.id === sub.linked_credit_card_id);
          return (
            <div
              key={sub.id}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
            >
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-medium text-slate-900 dark:text-slate-50">{sub.name}</p>
                  {card && (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                      {card.card_name}
                    </span>
                  )}
                  {!sub.is_active && (
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                      paused
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400">
                  Next billing {formatDate(sub.next_billing_date, user?.locale)}
                  {sub.reminder_days_before != null && ` · reminds ${sub.reminder_days_before}d before`}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <span className="font-mono text-sm text-slate-900 dark:text-slate-100">
                  <Money amountMinor={sub.amount_minor} currencyCode={sub.currency_code} />/mo
                </span>
                <button
                  onClick={() => update(sub.id, { is_active: !sub.is_active })}
                  className="text-xs text-slate-500 hover:underline dark:text-slate-400"
                >
                  {sub.is_active ? "Pause" : "Resume"}
                </button>
                <button onClick={() => remove(sub.id)} className="text-xs text-red-600 hover:underline">
                  Delete
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </main>
  );
}
