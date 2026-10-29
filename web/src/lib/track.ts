// Google Analytics (Firebase project) events for the buyer journey, using Google's recommended event names.
// No personal data: ids are model / variant ids, never names, emails or phone numbers.

type Params = Record<string, string | number | undefined | null>;

export function track(event: string, params: Params = {}) {
  if (typeof window === "undefined") return;
  const g = (window as unknown as { gtag?: (...a: unknown[]) => void }).gtag;
  if (!g) return;
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null));
  g("event", event, clean);
}

export const Track = {
  viewCar: (modelId: string, brand: string, city: string, fromInr?: number | null) =>
    track("view_item", { item_id: modelId, item_brand: brand, city, currency: "INR", value: fromInr ?? undefined }),
  pickVariant: (variantId: string, onRoadInr?: number | null) =>
    track("select_item", { item_id: variantId, currency: "INR", value: onRoadInr ?? undefined }),
  search: (q: string) => track("search", { search_term: q.slice(0, 80) }),
  saveCar: (variantId: string) => track("add_to_wishlist", { item_id: variantId }),
  quote: (variantId: string, city: string) => track("generate_lead", { item_id: variantId, city }),
  signUp: (method: string) => track("sign_up", { method }),
  login: (method: string) => track("login", { method }),
  news: (source: string, topic: string) => track("select_content", { content_type: "news", source, topic }),
};
