"use client";

// Search a model, then pick one of its variants. Used by the calculator and compare pages.

import { useState } from "react";
import useSWR from "swr";
import { Search } from "lucide-react";
import { fetcher, type ModelDetail, type Variant } from "@/lib/api";
import { lakh } from "@/lib/format";
import { Input, Select } from "@/components/ui";
import { useCity } from "@/components/city";

type Hit = { id: string; name: string; brand: string; brand_slug: string; from_inr: number | null };

export function CarPicker({ onPick }: { onPick: (v: Variant & { model: string; brand: string }) => void }) {
  const { city } = useCity();
  const [text, setText] = useState("");
  const [model, setModel] = useState<Hit | null>(null);
  const { data: hits } = useSWR<Hit[]>(text.trim().length >= 2 && !model ? `/search?q=${encodeURIComponent(text)}` : null, fetcher);
  const [, slug] = model ? model.id.split("/") : [];
  const { data: detail } = useSWR<ModelDetail>(model ? `/models/${model.brand_slug}/${slug}?city=${encodeURIComponent(city)}` : null, fetcher);

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-mute" />
        <Input value={model ? `${model.brand} ${model.name}` : text} placeholder="Search a car, e.g. Creta, Nexon, Seltos"
          onChange={(e) => { setModel(null); setText(e.target.value); }} className="pl-10" />
        {hits && hits.length > 0 && !model && (
          <div data-lenis-prevent className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-xl border border-line bg-panel shadow-2xl">
            {hits.map((h) => (
              <button key={h.id} onClick={() => setModel(h)} className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-white/5">
                <span className="text-white">{h.brand} {h.name}</span><span className="text-mute">{lakh(h.from_inr)}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      {detail && (
        <Select defaultValue="" onChange={(e) => {
          const v = detail.variants.find((x) => x.id === e.target.value);
          if (v) onPick({ ...v, model: detail.name, brand: detail.brand_name });
        }}>
          <option value="" disabled>Choose a variant ({detail.variants.length})</option>
          {detail.variants.map((v) => (
            <option key={v.id} value={v.id} disabled={!v.ex_showroom_inr}>
              {v.name} · {[v.fuel, v.transmission].filter(Boolean).join(" ")} · {lakh(v.ex_showroom_inr)}
            </option>
          ))}
        </Select>
      )}
    </div>
  );
}
