"use client";

// Live search: brands and models appear as you type; arrow keys + Enter, or click, open the result.

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import useSWR from "swr";
import { Search } from "lucide-react";
import { fetcher, type Brand } from "@/lib/api";
import { lakh } from "@/lib/format";
import { cn } from "@/components/ui";

type Hit = { id: string; name: string; brand: string; brand_slug: string; body_type: string | null; from_inr: number | null };
type Item = { key: string; href: string; title: string; sub: string; logo?: string | null };

export function SearchBox({ className, onDone, autoFocus }: { className?: string; onDone?: () => void; autoFocus?: boolean }) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => { const t = setTimeout(() => setDebounced(q.trim()), 150); return () => clearTimeout(t); }, [q]);
  useEffect(() => {
    const close = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const { data: brands } = useSWR<Brand[]>("/brands", fetcher);
  const { data: hits, isLoading } = useSWR<Hit[]>(debounced.length >= 2 ? `/search?q=${encodeURIComponent(debounced)}` : null, fetcher);

  const items: Item[] = useMemo(() => {
    const t = debounced.toLowerCase();
    if (t.length < 2) return [];
    const b = (brands ?? []).filter((x) => x.models > 0 && x.name.toLowerCase().includes(t)).slice(0, 3)
      .map((x) => ({ key: `b-${x.slug}`, href: `/cars?brand=${x.slug}`, title: x.name, sub: `Brand · ${x.models} models`, logo: x.logo }));
    const m = (hits ?? []).slice(0, 8).map((h) => ({ key: h.id, href: `/cars/${h.id}`, title: `${h.brand} ${h.name}`,
      sub: [h.body_type, h.from_inr ? `from ${lakh(h.from_inr)}` : "price on request"].filter(Boolean).join(" · ") }));
    return [...b, ...m];
  }, [debounced, brands, hits]);

  const go = (it: Item | undefined) => {
    if (!it) { if (q.trim()) { router.push(`/cars?q=${encodeURIComponent(q.trim())}`); } }
    else router.push(it.href);
    setOpen(false); setQ(""); onDone?.();
  };

  return (
    <div ref={box} className={cn("relative", className)}>
      <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 focus-within:border-accent/60">
        <Search className="h-4 w-4 shrink-0 text-mute" />
        <input value={q} autoFocus={autoFocus} placeholder="Search Creta, Nexon, Thar…" aria-label="Search cars"
          onChange={(e) => { setQ(e.target.value); setOpen(true); setActive(0); }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, items.length - 1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
            else if (e.key === "Enter") { e.preventDefault(); go(items[active]); }
            else if (e.key === "Escape") setOpen(false);
          }}
          className="h-9 w-full bg-transparent text-sm text-ink placeholder:text-mute/70 focus:outline-none" />
      </div>
      {open && debounced.length >= 2 && (
        <div data-lenis-prevent className="absolute right-0 z-50 mt-2 max-h-[70vh] w-full min-w-[320px] overflow-auto rounded-2xl border border-line bg-panel p-1.5 shadow-2xl">
          {items.length === 0 ? (
            <p className="px-3 py-3 text-sm text-mute">{isLoading ? "Searching…" : `No cars match “${debounced}”`}</p>
          ) : items.map((it, i) => (
            <button key={it.key} onMouseEnter={() => setActive(i)} onMouseDown={(e) => { e.preventDefault(); go(it); }}
              className={cn("flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left", i === active ? "bg-white/10" : "hover:bg-white/5")}>
              {it.logo !== undefined && (
                <span className="grid h-8 w-10 shrink-0 place-items-center rounded-md bg-white p-1">{it.logo && <img src={it.logo} alt="" className="max-h-6 w-auto" />}</span>
              )}
              <span className="min-w-0">
                <span className="block truncate text-sm text-ink">{it.title}</span>
                <span className="block truncate text-xs text-mute">{it.sub}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
