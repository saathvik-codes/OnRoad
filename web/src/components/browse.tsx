"use client";

// Browsing blocks: brand logo tiles, body-type icons and budget chips.

import Link from "next/link";
import useSWR from "swr";
import { motion } from "motion/react";
import { fetcher, type Brand } from "@/lib/api";
import { lakh } from "@/lib/format";
import { BIKE_BODY_TYPES, BODY_TYPES, BodyIcon } from "@/components/body-icons";
import { Skeleton } from "@/components/ui";
import { useCity, withCity } from "@/components/city";

export function BrandGrid({ limit, vehicleType = "car" }: { limit?: number; vehicleType?: string }) {
  const { city } = useCity();
  const url = withCity(`/brands?vehicle_type=${encodeURIComponent(vehicleType)}`, city);
  const { data } = useSWR<Brand[]>(url, fetcher);
  // the server orders brands by starting price, cheapest first (price on request last)
  const live = (data ?? []).filter((b) => b.models > 0);
  // Brands we track but can't price right now (site down / blocked) stay visible, greyed, with the reason on their page.
  const waiting = limit ? [] : (data ?? []).filter((b) => b.models === 0).sort((a, b) => a.name.localeCompare(b.name));
  const brands = [...live, ...waiting].slice(0, limit);
  const isBike = vehicleType === "bike";
  const basePath = isBike ? "/bikes" : "/cars";

  return (
    <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-6">
      {!data ? Array.from({ length: 12 }).map((_, i) => <Skeleton key={i} className="h-32" />) : brands.map((b, i) => (
        <motion.div key={b.slug} initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.03 }}>
          <Link href={`${basePath}?brand=${b.slug}`} title={b.models ? undefined : "Prices not available right now: open for the reason"}
            className={`group flex h-28 flex-col items-center justify-center gap-2 overflow-hidden rounded-2xl bg-white p-3 sm:h-32 sm:p-4 shadow-[0_10px_40px_-20px_rgba(255,255,255,0.25)] border border-line transition hover:-translate-y-1 hover:shadow-[0_18px_50px_-18px_rgba(255,77,46,0.6)] ${b.models ? "" : "opacity-60 grayscale"}`}>
            {b.logo ? <img src={b.logo} alt={b.name} className="h-9 w-full max-w-full object-contain transition group-hover:scale-105 sm:h-12" />
              : <span className="text-center font-bold text-slate-900 text-sm">{b.name}</span>}
            <span className="text-center text-[11px] font-medium leading-tight text-neutral-600">{b.name}<br />{b.from_inr ? `from ${lakh(b.from_inr)}` : b.models ? `${b.models} models` : "Prices unavailable"}</span>
          </Link>
        </motion.div>
      ))}
    </div>
  );
}

export function BodyRow({ vehicleType = "car" }: { vehicleType?: string }) {
  const isBike = vehicleType === "bike";
  const list = isBike ? BIKE_BODY_TYPES : BODY_TYPES;
  const basePath = isBike ? "/bikes" : "/cars";
  return (
    <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
      {list.map((t) => (
        <Link key={t} href={`${basePath}?body=${t}`} className="group flex flex-col items-center gap-2 rounded-2xl border border-line bg-panel px-3 py-5 transition hover:border-accent/60">
          <BodyIcon type={t} className="h-10 w-16 text-mute transition group-hover:text-accent" />
          <span className="text-sm font-semibold text-ink">{t}</span>
        </Link>
      ))}
    </div>
  );
}
