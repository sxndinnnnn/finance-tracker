# Data model

All monetary columns are stored as integer **minor units** (cents) to avoid
floating-point drift, paired with the currency's `decimal_places` from the
`currencies` table to render correctly (some currencies, like JPY, have 0
decimal places — another reason not to hardcode formatting).

## currencies
Seeded from `pycountry`/ISO 4217 — see `app/seed/seed_currencies.py`.
| column | type | notes |
|---|---|---|
| code | str(3) PK | e.g. `USD`, `LKR`, `EUR` |
| name | str | e.g. "Sri Lankan Rupee" |
| symbol | str | e.g. `Rs`, `$`, `€` — best-effort from Babel |
| decimal_places | int | e.g. 2 for USD, 0 for JPY |

## users
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| email | str, unique | |
| hashed_password | str | |
| full_name | str | |
| base_currency_code | FK → currencies.code | drives dashboard conversion |
| locale | str | BCP-47, e.g. `en-LK`, `de-DE` — drives number/date formatting |
| timezone | str | IANA tz, e.g. `Asia/Colombo` |
| default_reminder_days_before | int | user-level fallback for subscriptions |
| created_at | datetime | |

## categories
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| user_id | FK → users.id, nullable | null = system default, seeded once |
| name | str | user-editable |
| kind | enum(income, expense) | structural, not a localization concern |
| icon | str, nullable | |
| color | str, nullable | |

## recurrence_rules
One generic table reused by transactions, loans, leases, and subscriptions —
this is the piece that keeps "fixed vs variable" and billing cycles from
turning into duplicated enum logic in four different models.
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| frequency | enum(daily, weekly, monthly, yearly, custom) | |
| interval | int | e.g. every 2 weeks = frequency=weekly, interval=2 |
| by_weekday | str, nullable | e.g. `MO,WE,FR` |
| by_monthday | int, nullable | e.g. 15th of the month |
| rrule_string | str, nullable | raw RFC 5545 RRULE for anything the columns above can't express |
| start_date | date | |
| end_date | date, nullable | null = indefinite |

## accounts
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| user_id | FK | |
| name | str | |
| type | enum(bank, cash, wallet, credit_card) | |
| currency_code | FK → currencies.code | |
| opening_balance_minor | int | |
| created_at | datetime | |

## transactions
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| user_id | FK | |
| account_id | FK → accounts.id | |
| category_id | FK → categories.id | |
| type | enum(income, expense) | |
| classification | enum(fixed, variable) | |
| amount_minor | int | in the transaction's own currency |
| currency_code | FK → currencies.code | |
| exchange_rate_to_base | numeric, nullable | captured at entry time, freezes historical reports |
| description | str, nullable | |
| transaction_date | date | |
| recurrence_rule_id | FK → recurrence_rules.id, nullable | set only for fixed/recurring items |
| parent_transaction_id | FK → transactions.id, nullable | links a generated instance back to its recurring template |

## loans
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| user_id | FK | |
| name | str | |
| lender | str | |
| principal_minor | int | |
| currency_code | FK | |
| interest_rate | numeric | percent |
| interest_type | enum(fixed, variable) | |
| term_months | int | |
| start_date | date | |
| payment_amount_minor | int | |
| payment_recurrence_rule_id | FK → recurrence_rules.id | |
| linked_account_id | FK → accounts.id | where payments are drawn from |
| remaining_balance_minor | int | recomputed as payments post |

## credit_cards
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| user_id | FK | |
| account_id | FK → accounts.id | one-to-one; card *is* an account, this row adds card-specific fields |
| card_name | str | e.g. "Amex Platinum" |
| network | str | free text — card schemes vary by country/issuer |
| credit_limit_minor | int | |
| statement_day | int | day-of-month |
| due_day | int | day-of-month |
| current_balance_minor | int | |

## leases
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| user_id | FK | |
| name | str | |
| asset_description | str | |
| lessor | str | |
| monthly_payment_minor | int | |
| currency_code | FK | |
| start_date | date | |
| end_date | date, nullable | |
| payment_recurrence_rule_id | FK → recurrence_rules.id | |
| linked_account_id | FK → accounts.id | |

## subscriptions
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| user_id | FK | |
| name | str | |
| amount_minor | int | |
| currency_code | FK | |
| billing_recurrence_rule_id | FK → recurrence_rules.id | |
| next_billing_date | date | advanced by the reminder/billing job each cycle |
| linked_credit_card_id | FK → credit_cards.id, nullable | "which card is this on" |
| linked_account_id | FK → accounts.id, nullable | for non-card subscriptions |
| category_id | FK → categories.id, nullable | |
| reminder_days_before | int, nullable | overrides the user default when set |
| is_active | bool | |

## reminder_logs
| column | type | notes |
|---|---|---|
| id | UUID PK | |
| subscription_id | FK → subscriptions.id | |
| sent_at | datetime | |
| channel | enum(email) | room to add sms/push later |
| status | enum(sent, failed) | |

Guarantees this design gives you for free:
- Adding a new currency or country requires **zero code changes** — it's a
  seed refresh.
- Adding a new recurrence pattern (e.g. "every 2nd Tuesday") is a
  `recurrence_rules` row, not a new `if` branch in four models.
- Deleting a credit card cleanly surfaces every subscription that needs a
  new card, via `linked_credit_card_id`.
