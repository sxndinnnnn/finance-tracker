"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { Currency } from "@/types";

let cache: Currency[] | null = null;

export function useCurrencies() {
  const [currencies, setCurrencies] = useState<Currency[]>(cache ?? []);
  const [loading, setLoading] = useState(cache === null);

  useEffect(() => {
    if (cache) return;
    api
      .get<Currency[]>("/currencies")
      .then((data) => {
        cache = data;
        setCurrencies(data);
      })
      .finally(() => setLoading(false));
  }, []);

  return { currencies, loading };
}
