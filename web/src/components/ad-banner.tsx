"use client";

// Rotating banner of live manufacturer offers (from /api/campaigns: each slide is a real offer on the brand's own site,
// with its validity and source link). Renders nothing when there are no live offers.

import Link from "next/link";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { ChevronLeft, ChevronRight, ExternalLink, Zap } from "lucide-react";
import { fetcher } from "@/lib/api";
import { useCity, withCity } from "@/components/city";
import { cn } from "@/components/ui";

type Slide = { id: string; tag: string; title: string; highlight: string; description: string; valid_until: string | null;
  cta_text: string; cta_link: string; source_url: string | null; disclaimer: string };

export function AdBanner({ className }: { className?: string }) {
  const { city } = useCity();
  const { data } = useSWR<Slide[]>(withCity("/campaigns", city), fetcher);
  const [i, setI] = useState(0);
  const slides = data ?? [];
  useEffect(() => {
    if (slides.length < 2) return;
    const t = setInterval(() => setI((x) => (x + 1) % slides.length), 7000);
    return () => clearInterval(t);
  }, [slides.length]);
  if (!slides.length) return null;
  const s = slides[i % slides.length];

  return (
    <div className={cn("relative overflow-hidden rounded-3xl border border-line bg-panel p-6 sm:p-8", className)}>
      <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />
      <div className="relative flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
        <div className="max-w-2xl">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 text-[11px] font-bold tracking-wider text-accent">
            <Zap className="h-3 w-3" />{s.tag}
          </span>
          <h3 className="mt-3 font-[family-name:var(--font-display)] text-xl font-bold text-ink sm:text-2xl">{s.title}</h3>
          <p className="mt-1 text-2xl font-black text-good">{s.highlight}</p>
          {s.description && <p className="mt-2 line-clamp-2 text-sm text-mute">{s.description}</p>}
          <p className="mt-3 text-xs text-mute">
            {s.disclaimer}
            {s.source_url && <> · <a href={s.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-accent-2 hover:underline">source <ExternalLink className="h-3 w-3" /></a></>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {slides.length > 1 && (
            <>
              <button aria-label="Previous offer" onClick={() => setI((i - 1 + slides.length) % slides.length)} className="rounded-full border border-line p-2 text-mute hover:text-ink"><ChevronLeft className="h-4 w-4" /></button>
              <button aria-label="Next offer" onClick={() => setI((i + 1) % slides.length)} className="rounded-full border border-line p-2 text-mute hover:text-ink"><ChevronRight className="h-4 w-4" /></button>
            </>
          )}
          <Link href={s.cta_link} className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white">{s.cta_text}</Link>
        </div>
      </div>
    </div>
  );
}
