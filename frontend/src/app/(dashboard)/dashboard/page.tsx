"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";
import { useCurrencies } from "@/hooks/useCurrencies";
import { Money } from "@/components/Money";
import { formatDate } from "@/lib/currency";
import type { DashboardSummary } from "@/types";

function SummaryCard({ label, amountMinor, currencyCode }: { label: string; amountMinor: number; currencyCode: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 font-mono text-xl text-slate-900 dark:text-slate-100">
        <Money amountMinor={amountMinor} currencyCode={currencyCode} />
      </p>
    </div>
  );
}

export default function Page() {
  const { user } = useAuth();
  const { currencies } = useCurrencies();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<DashboardSummary>("/dashboard/summary")
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-slate-400">Loading…</p>;
  if (error || !summary) return <p className="text-sm text-red-600">{error ?? "Failed to load dashboard"}</p>;

  const base = summary.base_currency_code;
  const baseDecimalPlaces = currencies.find((c) => c.code === base)?.decimal_places ?? 2;
  const divisor = 10 ** baseDecimalPlaces;
  const numberFormat = new Intl.NumberFormat(user?.locale ?? "en-US", {
    minimumFractionDigits: baseDecimalPlaces,
    maximumFractionDigits: baseDecimalPlaces,
  });
  const tooltipFormatter = (value: number) => numberFormat.format(value);
  const trendData = summary.income_expense_trend.map((p) => ({
    month: p.month,
    Income: p.income_minor / divisor,
    Expense: p.expense_minor / divisor,
  }));
  const categoryData = summary.spending_by_category.map((c) => ({
    name: c.category_name,
    amount: c.amount_minor / divisor,
  }));

  return (
    <main>
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Dashboard</h1>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryCard label="Income this month" amountMinor={summary.month_income_minor} currencyCode={base} />
        <SummaryCard label="Expense this month" amountMinor={summary.month_expense_minor} currencyCode={base} />
        <SummaryCard label="Fixed expenses" amountMinor={summary.fixed_expense_minor} currencyCode={base} />
        <SummaryCard label="Variable expenses" amountMinor={summary.variable_expense_minor} currencyCode={base} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Income vs. expense trend</p>
          <div className="mt-2 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-100 dark:stroke-slate-800" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={tooltipFormatter} />
                <Legend />
                <Line type="monotone" dataKey="Income" stroke="#059669" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Expense" stroke="#dc2626" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Spending by category</p>
          <div className="mt-2 h-64">
            {categoryData.length === 0 ? (
              <p className="flex h-full items-center justify-center text-sm text-slate-400">
                No expenses this month yet.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-100 dark:stroke-slate-800" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={100} />
                  <Tooltip formatter={tooltipFormatter} />
                  <Bar dataKey="amount" fill="#334155" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Upcoming bills (next 30 days)</p>
        {summary.upcoming_bills.length === 0 ? (
          <p className="mt-2 text-sm text-slate-400">Nothing due soon.</p>
        ) : (
          <ul className="mt-2 divide-y divide-slate-100 dark:divide-slate-800">
            {summary.upcoming_bills.map((bill, i) => (
              <li key={i} className="flex items-center justify-between py-2 text-sm">
                <div>
                  <span className="font-medium text-slate-900 dark:text-slate-50">{bill.name}</span>{" "}
                  <span className="text-xs uppercase text-slate-400">{bill.kind}</span>
                  <p className="text-xs text-slate-400">{formatDate(bill.due_date, user?.locale)}</p>
                </div>
                <span className="font-mono text-slate-900 dark:text-slate-100">
                  <Money amountMinor={bill.amount_minor} currencyCode={bill.currency_code} />
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
