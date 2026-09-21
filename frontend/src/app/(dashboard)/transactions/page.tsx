"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useResource } from "@/hooks/useResource";
import { useAuth } from "@/hooks/useAuth";
import { useCurrencies } from "@/hooks/useCurrencies";
import { Money } from "@/components/Money";
import { formatDate } from "@/lib/currency";
import { ApiError } from "@/lib/api-client";
import type { Account, Category, Classification, Frequency, Transaction, TransactionType } from "@/types";

interface FormValues {
  account_id: string;
  category_id: string;
  type: TransactionType;
  classification: Classification;
  amount_major: number;
  transaction_date: string;
  description: string;
  frequency: Frequency;
  interval: number;
}

export default function Page() {
  const { user } = useAuth();
  const { items: accounts } = useResource<Account>("/accounts");
  const { items: categories } = useResource<Category>("/categories");
  const { items: transactions, loading, create, remove } = useResource<Transaction>("/transactions");
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
      type: "expense",
      classification: "variable",
      transaction_date: new Date().toISOString().slice(0, 10),
      frequency: "monthly",
      interval: 1,
    },
  });

  const type = watch("type");
  const classification = watch("classification");
  const accountId = watch("account_id");
  const account = accounts.find((a) => a.id === accountId);
  const decimalPlaces = currencies.find((c) => c.code === account?.currency_code)?.decimal_places ?? 2;
  const visibleCategories = categories.filter((c) => c.kind === type);

  async function onSubmit(values: FormValues) {
    setServerError(null);
    try {
      await create({
        account_id: values.account_id,
        category_id: values.category_id,
        type: values.type,
        classification: values.classification,
        amount_minor: Math.round(values.amount_major * 10 ** decimalPlaces),
        transaction_date: values.transaction_date,
        description: values.description || undefined,
        recurrence:
          values.classification === "fixed"
            ? { frequency: values.frequency, interval: values.interval, start_date: values.transaction_date }
            : undefined,
      });
      reset({
        ...values,
        amount_major: 0,
        description: "",
      });
      setShowForm(false);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong");
    }
  }

  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Transactions</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          {showForm ? "Cancel" : "New transaction"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-4 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2 dark:border-slate-800 dark:bg-slate-900"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Account</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("account_id", { required: true })}
            >
              <option value="">Select an account</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.currency_code})
                </option>
              ))}
            </select>
            {accounts.length === 0 && (
              <p className="mt-1 text-xs text-amber-600">Create an account first.</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Type</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("type")}
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Category</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("category_id", { required: true })}
            >
              <option value="">Select a category</option>
              {visibleCategories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Amount</label>
            <input
              type="number"
              step="0.01"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("amount_major", { valueAsNumber: true, required: true, min: 0.01 })}
            />
            {errors.amount_major && <p className="mt-1 text-xs text-red-600">Enter an amount greater than 0</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Date</label>
            <input
              type="date"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("transaction_date", { required: true })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Classification
            </label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("classification")}
            >
              <option value="variable">Variable (one-off)</option>
              <option value="fixed">Fixed (recurring)</option>
            </select>
          </div>

          {classification === "fixed" && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Repeats</label>
                <select
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                  {...register("frequency")}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  Every N periods
                </label>
                <input
                  type="number"
                  min={1}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                  {...register("interval", { valueAsNumber: true, min: 1 })}
                />
              </div>
            </>
          )}

          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Description (optional)
            </label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              {...register("description")}
            />
          </div>

          {serverError && <p className="sm:col-span-2 text-sm text-red-600">{serverError}</p>}

          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900"
            >
              {isSubmitting ? "Saving…" : "Add transaction"}
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 space-y-2">
        {loading && <p className="text-sm text-slate-400">Loading…</p>}
        {!loading && transactions.length === 0 && (
          <p className="text-sm text-slate-400">No transactions yet.</p>
        )}
        {transactions.map((tx) => {
          const category = categories.find((c) => c.id === tx.category_id);
          return (
            <div
              key={tx.id}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
            >
              <div>
                <p className="font-medium text-slate-900 dark:text-slate-50">
                  {tx.description || category?.name || "Transaction"}
                </p>
                <p className="text-xs text-slate-400">
                  {formatDate(tx.transaction_date, user?.locale)} · {category?.name ?? "Uncategorized"} ·{" "}
                  {tx.classification}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={
                    "font-mono text-sm " +
                    (tx.type === "income" ? "text-emerald-600" : "text-slate-900 dark:text-slate-100")
                  }
                >
                  {tx.type === "income" ? "+" : "-"}
                  <Money amountMinor={tx.amount_minor} currencyCode={tx.currency_code} />
                </span>
                <button onClick={() => remove(tx.id)} className="text-xs text-red-600 hover:underline">
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
