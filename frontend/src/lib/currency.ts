/**
 * Locale- and currency-aware formatting, driven entirely by Intl — no
 * hand-written symbol tables. `currencyCode` comes from the currencies
 * endpoint (backed by ISO 4217), `locale` from the signed-in user's profile.
 */
export function formatAmountMinor(
  amountMinor: number,
  currencyCode: string,
  locale: string = "en-US"
): string {
  const major = amountMinor / 100; // refine per-currency using decimal_places from /currencies if needed
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currencyCode,
  }).format(major);
}

export function listBrowserCurrencies(): string[] {
  // Fallback/dev helper — the canonical list is the backend's /currencies
  // endpoint (seeded from pycountry), not this.
  // @ts-expect-error — supportedValuesOf is newer than some TS lib targets
  return Intl.supportedValuesOf?.("currency") ?? [];
}
