"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import useSWR from "swr";
import { X } from "lucide-react";
import { fetcher, type Breakdown } from "@/lib/api";
import { inr, lakh } from "@/lib/format";
import { CarPicker } from "@/components/car-picker";
import { useCity, withCity } from "@/components/city";
import { Card, SectionTitle, Skeleton } from "@/components/ui";

type Row = { id: string; name: string; model: string; brand: string; brand_slug: string; model_id: string; fuel: string | null;
  transmission: string | null; engine_cc: number | null; battery_kwh: number | null; seats: number | null; onroad: (Breakdown & { ex_showroom_inr: number }) | null };

function CompareInner() {
  const sp = useSearchParams();
  const router = useRouter();
  const ids = (sp.get("ids") ?? "").split(",").filter(Boolean);
  const { city } = useCity();
  const { data, isLoading } = useSWR<Row[]>(ids.length ? withCity(`/compare?ids=${encodeURIComponent(ids.join(","))}`, city) : null, fetcher);
  const setIds = (next: string[]) => router.replace(next.length ? `/compare?ids=${encodeURIComponent(next.join(","))}` : "/compare", { scroll: false });
  const rows = data ?? [];
  const cheapest = rows.reduce<number | null>((m, r) => (r.onroad && (m === null || r.onroad.total_inr < m) ? r.onroad.total_inr : m), null);

  const line = (r: Row, label: string) => r.onroad?.lines.find((l) => l.label.toLowerCase().startsWith(label))?.amount_inr ?? null;
  const specs: [string, (r: Row) => string][] = [
    ["Ex-showroom", (r) => inr(r.onroad?.ex_showroom_inr)],
    ["Road tax", (r) => inr(line(r, "road tax"))],
    ["Insurance (3-yr TP)", (r) => inr(line(r, "insurance: third"))],
    ["Insurance (own damage)", (r) => inr(line(r, "insurance: own"))],
    ["TCS (refundable)", (r) => inr(r.onroad?.refundable_inr)],
    ["Fuel", (r) => r.fuel ?? "—"],
    ["Transmission", (r) => r.transmission ?? "—"],
    ["Engine / battery", (r) => (r.engine_cc ? `${r.engine_cc} cc` : r.battery_kwh ? `${r.battery_kwh} kWh` : "—")],
    ["Seats", (r) => (r.seats ? String(r.seats) : "—")],
  ];

  return (
    <main className="mx-auto max-w-7xl px-5 pt-28 pb-24">
      <SectionTitle eyebrow="Compare" title="Side by side, on-road" sub={`Up to four variants with the full on-road price for ${city}, not just ex-showroom.`} />
      {ids.length < 4 && (
        <Card className="mt-8 max-w-xl p-5"><CarPicker onPick={(v) => !ids.includes(v.id) && setIds([...ids, v.id])} /></Card>
      )}
      {isLoading && <Skeleton className="mt-8 h-96" />}
      {rows.length > 0 && (
        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-[640px] border-separate border-spacing-0 text-sm">
            <thead>
              <tr>
                <th className="w-44" />
                {rows.map((r) => (
                  <th key={r.id} className="rounded-t-2xl border border-b-0 border-line bg-panel p-4 text-left align-top">
                    <div className="flex items-start justify-between gap-2">
                      <Link href={`/cars/${r.model_id}`} className="hover:text-accent">
                        <p className="text-xs font-normal text-mute">{r.brand}</p>
                        <p className="font-[family-name:var(--font-display)] text-lg text-white">{r.model}</p>
                        <p className="font-normal text-white/70">{r.name}</p>
                      </Link>
                      <button onClick={() => setIds(ids.filter((i) => i !== r.id))} aria-label="Remove" className="text-mute hover:text-white"><X className="h-4 w-4" /></button>
                    </div>
                    <p className={`mt-3 text-2xl font-bold ${r.onroad?.total_inr === cheapest ? "text-emerald-300" : "text-white"}`}>{lakh(r.onroad?.total_inr)}</p>
                    <p className="text-xs font-normal text-mute">on-road {r.onroad?.total_inr === cheapest && rows.length > 1 ? "· cheapest" : ""}</p>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {specs.map(([label, fn]) => (
                <tr key={label}>
                  <td className="border-t border-line py-3 pr-4 text-mute">{label}</td>
                  {rows.map((r) => <td key={r.id} className="border-x border-t border-line bg-panel/60 p-4 text-white">{fn(r)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!ids.length && <p className="mt-6 text-mute">Add a car to start comparing.</p>}
    </main>
  );
}

export default function ComparePage() {
  return <Suspense><CompareInner /></Suspense>;
}
