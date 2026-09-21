/**
 * Locale- and currency-aware formatting, driven entirely by Intl — no
 * hand-written symbol tables. `currencyCode` comes from the currencies
 * endpoint (backed by ISO 4217), `locale` from the signed-in user's profile.
 */
export function formatAmountMinor(
  amountMinor: number,
  currencyCode: string,
  locale: string = "en-US",
  decimalPlaces: number = 2
): string {
  const major = amountMinor / 10 ** decimalPlaces;
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: currencyCode,
      minimumFractionDigits: decimalPlaces,
      maximumFractionDigits: decimalPlaces,
    }).format(major);
  } catch {
    // Locale or currency code Intl doesn't recognize (e.g. a non-circulating
    // ISO 4217 code) — fall back to a plain number plus the raw code.
    return `${major.toFixed(decimalPlaces)} ${currencyCode}`;
  }
}

export function majorToMinor(amountMajor: number, decimalPlaces: number = 2): number {
  return Math.round(amountMajor * 10 ** decimalPlaces);
}

export function formatDate(isoDate: string, locale: string = "en-US"): string {
  try {
    return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(isoDate));
  } catch {
    return isoDate;
  }
}

export function listBrowserCurrencies(): string[] {
  // Fallback/dev helper — the canonical list is the backend's /currencies
  // endpoint (seeded from pycountry), not this.
  return Intl.supportedValuesOf?.("currency") ?? [];
}
