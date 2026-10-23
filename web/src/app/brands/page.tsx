"use client";

import { Suspense, useState } from "react";
import useSWR from "swr";
import { fetcher, type Brand } from "@/lib/api";
import { useCity, withCity } from "@/components/city";
import { useSearchParams, useRouter } from "next/navigation";
import { Car, Bike } from "lucide-react";
import { BodyRow, BrandGrid } from "@/components/browse";
import { SectionTitle, cn } from "@/components/ui";

function BrandsInner() {
  const { city } = useCity();
  const { data: cars } = useSWR<Brand[]>(withCity("/brands?vehicle_type=car", city), fetcher);
  const { data: bikes } = useSWR<Brand[]>(withCity("/brands?vehicle_type=bike", city), fetcher);
  const live = (b?: Brand[]) => (b ? String(b.filter((x) => x.models > 0).length) : "…");
  const searchParams = useSearchParams();
  const router = useRouter();
  const typeParam = searchParams.get("type");
  const [vehicleType, setVehicleType] = useState<"car" | "bike">(typeParam === "bike" ? "bike" : "car");

  const handleTypeChange = (type: "car" | "bike") => {
    setVehicleType(type);
    const params = new URLSearchParams(searchParams.toString());
    params.set("type", type);
    router.replace(`/brands?${params.toString()}`, { scroll: false });
  };

  return (
    <main className="mx-auto max-w-7xl px-5 pt-28 pb-24">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <SectionTitle 
          eyebrow="Manufacturer Directory" 
          title={vehicleType === "car" ? "All Car Brands in India" : "All Two-Wheeler Brands in India"} 
          sub={vehicleType === "car" 
            ? "Tap any car manufacturer to see its full model lineup, variant prices, and local dealer network." 
            : "Tap any motorcycle or scooter brand to see its full lineup, starting prices, and showroom network."
          } 
        />

        {/* Vehicle Category Toggle */}
        <div className="inline-flex shrink-0 items-center rounded-2xl border border-line bg-panel p-1.5 shadow-sm">
          <button
            type="button"
            onClick={() => handleTypeChange("car")}
            className={cn(
              "flex items-center gap-2 rounded-xl px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
              vehicleType === "car"
                ? "bg-accent text-white shadow-md shadow-accent/25"
                : "text-mute hover:text-white"
            )}
          >
            <Car className="h-4 w-4" />
            <span>Cars ({live(cars)})</span>
          </button>
          <button
            type="button"
            onClick={() => handleTypeChange("bike")}
            className={cn(
              "flex items-center gap-2 rounded-xl px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
              vehicleType === "bike"
                ? "bg-accent text-white shadow-md shadow-accent/25"
                : "text-mute hover:text-white"
            )}
          >
            <Bike className="h-4 w-4" />
            <span>Two-Wheelers ({live(bikes)})</span>
          </button>
        </div>
      </div>

      <div className="mt-10">
        <BrandGrid vehicleType={vehicleType} />
      </div>

      <h3 className="mt-16 mb-5 font-[family-name:var(--font-display)] text-2xl font-bold text-white">
        Or browse by {vehicleType === "car" ? "car" : "bike"} body type
      </h3>
      <BodyRow vehicleType={vehicleType} />
    </main>
  );
}

export default function BrandsPage() {
  return <Suspense><BrandsInner /></Suspense>;
}
