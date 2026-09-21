// Shared TypeScript types, mirroring backend/app/schemas.

export interface Currency {
  code: string;
  name: string;
  symbol: string;
  decimal_places: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  base_currency_code: string;
  locale: string;
  timezone: string;
  default_reminder_days_before: number;
  created_at: string;
}

export type CategoryKind = "income" | "expense";

export interface Category {
  id: string;
  user_id: string | null;
  name: string;
  kind: CategoryKind;
  icon: string | null;
  color: string | null;
  is_default: boolean;
}

export type AccountType = "bank" | "cash" | "wallet" | "credit_card";

export interface Account {
  id: string;
  user_id: string;
  name: string;
  type: AccountType;
  currency_code: string;
  opening_balance_minor: number;
  current_balance_minor: number;
  created_at: string;
}

export type TransactionType = "income" | "expense";
export type Classification = "fixed" | "variable";
export type Frequency = "daily" | "weekly" | "monthly" | "yearly" | "custom";

export interface RecurrenceRule {
  id: string;
  frequency: Frequency;
  interval: number;
  by_weekday: string | null;
  by_monthday: number | null;
  rrule_string: string | null;
  start_date: string;
  end_date: string | null;
}

export interface RecurrenceRuleInput {
  frequency: Frequency;
  interval: number;
  by_weekday?: string | null;
  by_monthday?: number | null;
  rrule_string?: string | null;
  start_date: string;
  end_date?: string | null;
}

export interface Transaction {
  id: string;
  user_id: string;
  account_id: string;
  category_id: string;
  type: TransactionType;
  classification: Classification;
  amount_minor: number;
  currency_code: string;
  exchange_rate_to_base: number | null;
  description: string | null;
  transaction_date: string;
  recurrence_rule_id: string | null;
  parent_transaction_id: string | null;
  recurrence: RecurrenceRule | null;
}

export type InterestType = "fixed" | "variable";

export interface Loan {
  id: string;
  user_id: string;
  name: string;
  lender: string;
  principal_minor: number;
  currency_code: string;
  interest_rate: number;
  interest_type: InterestType;
  term_months: number;
  start_date: string;
  payment_amount_minor: number;
  payment_recurrence_rule_id: string;
  linked_account_id: string;
  remaining_balance_minor: number;
  recurrence: RecurrenceRule | null;
}

export interface CreditCard {
  id: string;
  user_id: string;
  account_id: string;
  card_name: string;
  network: string | null;
  credit_limit_minor: number;
  statement_day: number;
  due_day: number;
  current_balance_minor: number;
  account: Account;
}

export interface Lease {
  id: string;
  user_id: string;
  name: string;
  asset_description: string | null;
  lessor: string;
  monthly_payment_minor: number;
  currency_code: string;
  start_date: string;
  end_date: string | null;
  payment_recurrence_rule_id: string;
  linked_account_id: string;
  recurrence: RecurrenceRule | null;
}

export interface Subscription {
  id: string;
  user_id: string;
  name: string;
  amount_minor: number;
  currency_code: string;
  billing_recurrence_rule_id: string;
  next_billing_date: string;
  linked_credit_card_id: string | null;
  linked_account_id: string | null;
  category_id: string | null;
  reminder_days_before: number | null;
  is_active: boolean;
  recurrence: RecurrenceRule | null;
}

export interface DashboardSummary {
  base_currency_code: string;
  month_income_minor: number;
  month_expense_minor: number;
  fixed_expense_minor: number;
  variable_expense_minor: number;
  upcoming_bills: {
    name: string;
    kind: string;
    amount_minor: number;
    currency_code: string;
    due_date: string;
  }[];
  income_expense_trend: { month: string; income_minor: number; expense_minor: number }[];
  spending_by_category: { category_name: string; amount_minor: number }[];
}
