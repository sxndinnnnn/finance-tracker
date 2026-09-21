"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useResource } from "@/hooks/useResource";
import { useCurrencies } from "@/hooks/useCurrencies";
import { useAuth } from "@/hooks/useAuth";
import { Money } from "@/components/Money";
import { ApiError } from "@/lib/api-client";
import type { CreditCard } from "@/types";

interface FormValues {
  card_name: string;
  network: string;
  currency_code: string;
  credit_limit_major: number;
  statement_day: number;
  due_day: number;
}

export default function Page() {
  const { user } = useAuth();
  const { items: cards, loading, create, remove } = useResource<CreditCard>("/credit-cards");
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
    defaultValues: { currency_code: user?.base_currency_code, statement_day: 1, due_day: 15 },
  });

  const decimalPlaces = currencies.find((c) => c.code === watch("currency_code"))?.decimal_places ?? 2;

  async function onSubmit(values: FormValues) {
    setServerError(null);
    try {
      await create({
        card_name: values.card_name,
        network: values.network || undefined,
        currency_code: values.currency_code,
        credit_limit_minor: Math.round(values.credit_limit_major * 10 ** decimalPlaces),
        statement_day: values.statement_day,
        due_day: values.due_day,
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
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Credit Cards</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          {showForm ? "Cancel" : "New card"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-4 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2 dark:border-slate-800 dark:bg-slate-900"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Card name</label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("card_name", { required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Network (optional)
            </label>
            <input
              placeholder="Visa, Mastercard, local scheme…"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("network")}
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
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Credit limit</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("credit_limit_major", { valueAsNumber: true, required: true })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Statement day
            </label>
            <input
              type="number"
              min={1}
              max={31}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("statement_day", { valueAsNumber: true, min: 1, max: 31 })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Due day</label>
            <input
              type="number"
              min={1}
              max={31}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("due_day", { valueAsNumber: true, min: 1, max: 31 })}
            />
          </div>
          {serverError && <p className="sm:col-span-2 text-sm text-red-600">{serverError}</p>}
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900"
            >
              {isSubmitting ? "Saving…" : "Add card"}
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {loading && <p className="text-sm text-slate-400">Loading…</p>}
        {!loading && cards.length === 0 && <p className="text-sm text-slate-400">No credit cards yet.</p>}
        {cards.map((card) => (
          <div
            key={card.id}
            className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-slate-900 dark:text-slate-50">{card.card_name}</p>
                <p className="text-xs text-slate-400">{card.network || "—"}</p>
              </div>
              <button onClick={() => remove(card.id)} className="text-xs text-red-600 hover:underline">
                Delete
              </button>
            </div>
            <div className="mt-3 flex items-baseline justify-between">
              <span className="font-mono text-lg text-slate-900 dark:text-slate-100">
                <Money amountMinor={card.current_balance_minor} currencyCode={card.account.currency_code} />
              </span>
              <span className="text-xs text-slate-400">
                limit <Money amountMinor={card.credit_limit_minor} currencyCode={card.account.currency_code} />
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-400">
              Statement day {card.statement_day} · Due day {card.due_day}
            </p>
            {card.linked_subscriptions && card.linked_subscriptions.length > 0 && (
              <div className="mt-3 border-t border-slate-100 pt-2 dark:border-slate-800">
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Subscriptions on this card
                </p>
                <ul className="mt-1 space-y-0.5">
                  {card.linked_subscriptions.map((sub) => (
                    <li key={sub.id} className="text-xs text-slate-600 dark:text-slate-300">
                      {sub.name} —{" "}
                      <Money amountMinor={sub.amount_minor} currencyCode={sub.currency_code} />
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
