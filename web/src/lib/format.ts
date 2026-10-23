// Indian price formatting: ₹ 7.49 Lakh, ₹ 1.25 Crore, and full rupee amounts with Indian digit grouping.

export function inr(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return "₹" + Math.round(n).toLocaleString("en-IN");
}

export function lakh(n: number | null | undefined): string {
  if (n === null || n === undefined) return "Price on request";
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2).replace(/\.?0+$/, "")} Cr`;
  return `₹${(n / 1e5).toFixed(2).replace(/\.?0+$/, "")} L`;
}

export function range(a: number | null | undefined, b: number | null | undefined): string {
  if (!a) return "Price on request";
  if (!b || a === b) return lakh(a);
  return `${lakh(a)} – ${lakh(b).replace("₹", "")}`;
}

export function ago(iso: string | null | undefined): string {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return `${Math.max(1, Math.round(s / 60))} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  return `${Math.round(s / 86400)} d ago`;
}

// Paint colours for the 3D stage (stable per model so a model always shows the same colour)
const PAINTS = ["#c1121f", "#1f4fd1", "#e6e8ec", "#0f1115", "#7a7f88", "#0d6b5c", "#b36b00", "#5b2a86", "#a3a8b0", "#8c1c13"];
export function paintFor(id: string): string {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return PAINTS[h % PAINTS.length];
}
