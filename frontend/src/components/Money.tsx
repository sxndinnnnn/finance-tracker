"use client";

import { useCurrencies } from "@/hooks/useCurrencies";
import { useAuth } from "@/hooks/useAuth";
import { formatAmountMinor } from "@/lib/currency";

export function Money({ amountMinor, currencyCode }: { amountMinor: number; currencyCode: string }) {
  const { user } = useAuth();
  const { currencies } = useCurrencies();
  const decimalPlaces = currencies.find((c) => c.code === currencyCode)?.decimal_places ?? 2;
  return <>{formatAmountMinor(amountMinor, currencyCode, user?.locale ?? "en-US", decimalPlaces)}</>;
}
