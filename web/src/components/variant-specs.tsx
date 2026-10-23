"use client";

// Specs + equipment for one variant, ONLY as the manufacturer publishes them (/api/variant-specs, every row sourced).
// Each listed feature gets an explanatory illustration so buyers understand what it is. Nothing is estimated.

import { useMemo, useState } from "react";
import useSWR from "swr";
import { BookOpen, CheckCircle2, ExternalLink, Info, Search } from "lucide-react";
import { fetcher, type Variant } from "@/lib/api";
import { ago } from "@/lib/format";
import { EquipmentArt } from "@/components/equipment-art";
import { imgSrc } from "@/components/car-image";
import { cn, Skeleton } from "@/components/ui";

type Spec = { grp: string; key: string; label: string; value: string; source_url: string; fetched_at: string };
type Feature = { key: string; label: string; source_url: string };
type Photo = { key?: string; image_url: string; source_url: string; brand?: string };
type Payload = { specs: Spec[]; features: Feature[]; model_url: string | null; photos?: Record<string, Photo>;
  basics: { fuel: string | null; transmission: string | null; engine_cc: number | null; battery_kwh: number | null; seats: number | null } };

type Cat = "safety" | "tech" | "comfort" | "styling" | "riding";
const FEATURE_INFO: Record<string, { cat: Cat; title: string; what: string }> = {
  airbags_6: { cat: "safety", title: "6 airbags", what: "Front, side and curtain airbags cushion the driver and passengers in front and side impacts." },
  airbags_2: { cat: "safety", title: "Dual front airbags", what: "Airbags for the driver and front passenger in a frontal crash." },
  esc: { cat: "safety", title: "Electronic Stability Control", what: "Brakes individual wheels automatically to stop the car skidding in a sudden swerve." },
  hill_hold: { cat: "safety", title: "Hill-hold assist", what: "Holds the brakes for a moment on a slope so the car doesn't roll back." },
  tpms: { cat: "safety", title: "Tyre pressure monitor", what: "Warns you on the dashboard when a tyre is losing air." },
  isofix: { cat: "safety", title: "ISOFIX child-seat mounts", what: "Metal anchors that lock a child seat in place without using the seat belt." },
  rear_parking_sensors: { cat: "safety", title: "Rear parking sensors", what: "Beep faster as you reverse closer to an obstacle." },
  front_parking_sensors: { cat: "safety", title: "Front parking sensors", what: "Warn you about obstacles close to the front bumper." },
  rear_camera: { cat: "safety", title: "Reversing camera", what: "Shows what is behind the car on the screen when you reverse." },
  camera_360: { cat: "safety", title: "360° camera", what: "Cameras on all four sides stitched into a bird's-eye view for tight parking." },
  adas: { cat: "safety", title: "ADAS (driver assistance)", what: "Radar and cameras that can brake for collisions, keep you in lane and follow traffic." },
  blind_spot_monitor: { cat: "safety", title: "Blind-spot monitor", what: "Lights up in the mirror when a vehicle is where you can't see before changing lanes." },
  rear_disc_brakes: { cat: "safety", title: "Rear disc brakes", what: "Disc brakes on the rear wheels too, for stronger, steadier stopping." },
  auto_headlamps: { cat: "safety", title: "Auto headlamps", what: "Headlamps switch on by themselves at dusk or in tunnels." },
  rain_sensing_wipers: { cat: "safety", title: "Rain-sensing wipers", what: "Wipers start and change speed on their own when it rains." },
  electric_parking_brake: { cat: "safety", title: "Electric parking brake", what: "A button replaces the hand-brake lever, often with auto-hold in traffic." },
  touchscreen: { cat: "tech", title: "Touchscreen infotainment", what: "Central screen for music, navigation, calls and car settings." },
  digital_cluster: { cat: "tech", title: "Digital instrument cluster", what: "A screen behind the steering wheel in place of analogue dials." },
  android_auto_carplay: { cat: "tech", title: "Android Auto / Apple CarPlay", what: "Shows your phone's maps, music and messages on the car's screen over a cable." },
  wireless_android_auto_carplay: { cat: "tech", title: "Wireless Android Auto / CarPlay", what: "The same phone mirroring without plugging in a cable." },
  connected_car: { cat: "tech", title: "Connected-car app", what: "Check location, lock / unlock and get alerts from a phone app via the car's built-in SIM." },
  wireless_charger: { cat: "tech", title: "Wireless phone charger", what: "Charge a compatible phone by placing it on the pad." },
  premium_audio: { cat: "tech", title: "Premium sound system", what: "A branded speaker system with more speakers and an amplifier." },
  hud: { cat: "tech", title: "Head-up display", what: "Speed and directions projected near your line of sight." },
  cruise_control: { cat: "tech", title: "Cruise control", what: "Holds a set speed on highways without pressing the accelerator." },
  keyless_entry: { cat: "tech", title: "Keyless entry", what: "Lock and unlock without taking the key out of your pocket." },
  push_button_start: { cat: "tech", title: "Push-button start", what: "Start the engine with a button while the key stays in your pocket." },
  remote_start: { cat: "tech", title: "Remote engine start", what: "Start the car (and its AC) from the key or app before you get in." },
  auto_climate: { cat: "comfort", title: "Automatic climate control", what: "Set a temperature and the AC adjusts fan and cooling on its own." },
  rear_ac_vents: { cat: "comfort", title: "Rear AC vents", what: "Air-conditioning vents for the back-seat passengers." },
  ventilated_seats: { cat: "comfort", title: "Ventilated seats", what: "Fans blow air through perforated seats to keep your back cool." },
  powered_driver_seat: { cat: "comfort", title: "Powered driver seat", what: "Adjust the driver's seat with electric switches." },
  sunroof: { cat: "comfort", title: "Sunroof", what: "A glass panel in the roof that tilts or slides open." },
  panoramic_sunroof: { cat: "comfort", title: "Panoramic sunroof", what: "A large glass roof over both rows; usually the front part opens." },
  ambient_lighting: { cat: "comfort", title: "Ambient lighting", what: "Soft coloured mood lights along the dashboard and doors." },
  cooled_glovebox: { cat: "comfort", title: "Cooled glovebox", what: "The AC chills the glovebox to keep drinks cool." },
  rear_armrest: { cat: "comfort", title: "Rear armrest", what: "Fold-down armrest, often with cup holders, for back-seat comfort." },
  height_adjustable_seat: { cat: "comfort", title: "Height-adjustable driver seat", what: "Raise or lower the driver's seat for a better view of the road." },
  led_headlamps: { cat: "styling", title: "LED headlamps", what: "Brighter, whiter and longer-lasting headlights than halogen bulbs." },
  led_drl: { cat: "styling", title: "LED daytime running lamps", what: "Light strips that stay on so others see you, even in daylight." },
  alloy_wheels: { cat: "styling", title: "Alloy wheels", what: "Lighter, better-looking wheels in place of steel wheels with covers." },
  fog_lamps: { cat: "styling", title: "Fog lamps", what: "Low, wide lamps that light the road edge in fog and heavy rain." },
  roof_rails: { cat: "styling", title: "Roof rails", what: "Bars on the roof for carriers and luggage boxes." },
  abs_dual: { cat: "riding", title: "Dual-channel ABS", what: "Stops both wheels locking under hard braking, so the bike stays steerable." },
  abs_single: { cat: "riding", title: "Single-channel ABS", what: "Anti-lock braking on the front wheel." },
  cbs: { cat: "riding", title: "Combined braking (CBS)", what: "One lever applies both brakes together for steadier stops." },
  front_disc: { cat: "riding", title: "Front disc brake", what: "Stronger, more predictable braking than a drum brake." },
  tft_display: { cat: "riding", title: "TFT colour display", what: "A colour screen for speed, trip data and navigation." },
  bluetooth_console: { cat: "riding", title: "Bluetooth console", what: "Pairs with your phone for call alerts and turn-by-turn directions." },
  usb_charging: { cat: "riding", title: "USB charging", what: "Charge your phone while you ride." },
  traction_control: { cat: "riding", title: "Traction control", what: "Cuts power when the rear wheel starts to spin on slippery roads." },
  ride_modes: { cat: "riding", title: "Ride modes", what: "Switch engine response and ABS for city, rain or sport riding." },
  slipper_clutch: { cat: "riding", title: "Slipper clutch", what: "Stops the rear wheel hopping on quick downshifts and lightens the clutch." },
  led_lamps_2w: { cat: "riding", title: "LED lamps", what: "LED headlamp and tail-lamp for better visibility." },
};

const CATS: { id: Cat; label: string }[] = [
  { id: "safety", label: "Safety" }, { id: "tech", label: "Tech" }, { id: "comfort", label: "Comfort" },
  { id: "styling", label: "Styling" }, { id: "riding", label: "Riding" },
];
const GROUP_ORDER = ["Engine", "Performance", "Efficiency", "Battery", "Capacity", "Dimensions", "Chassis"];
const rank = (g: string) => (GROUP_ORDER.includes(g) ? GROUP_ORDER.indexOf(g) : 99);

interface Props { variant: Variant; modelName: string; brandName: string; bodyType?: string | null; vehicleType?: string | null }

export function VariantSpecs({ variant, modelName, brandName, vehicleType }: Props) {
  const isBike = vehicleType === "bike";
  const [tab, setTab] = useState<"equipment" | "specs" | "guide">("equipment");
  const [cat, setCat] = useState<Cat | "all">("all");
  const [q, setQ] = useState("");
  const { data, isLoading } = useSWR<Payload>(`/variant-specs?variant_id=${encodeURIComponent(variant.id)}`, fetcher);
  const { data: mf } = useSWR<{ total_variants: number; features: { key: string; label: string; variants: number; photo: string | null }[] }>(
    tab === "guide" ? `/model-features?model_id=${encodeURIComponent(variant.model_id)}` : null, fetcher);

  const known = useMemo(() => (data?.features ?? []).filter((f) => FEATURE_INFO[f.key]), [data]);
  const other = useMemo(() => (data?.features ?? []).filter((f) => !FEATURE_INFO[f.key]), [data]);
  const shown = known.filter((f) => (cat === "all" || FEATURE_INFO[f.key].cat === cat)
    && (!q || `${f.label} ${FEATURE_INFO[f.key].title}`.toLowerCase().includes(q.toLowerCase())));
  const groups = useMemo(() => {
    const g = new Map<string, Spec[]>();
    for (const s of data?.specs ?? []) g.set(s.grp, [...(g.get(s.grp) ?? []), s]);
    return [...g.entries()].sort((a, b) => rank(a[0]) - rank(b[0]));
  }, [data]);
  const source = data?.specs[0]?.source_url ?? data?.features[0]?.source_url ?? null;
  const asOf = data?.specs[0]?.fetched_at;
  const hasData = Boolean(data && (data.specs.length || data.features.length));
  const b = data?.basics;
  const chips = [b?.fuel ?? variant.fuel, b?.transmission ?? variant.transmission,
    (b?.engine_cc ?? variant.engine_cc) ? `${b?.engine_cc ?? variant.engine_cc} cc` : null,
    (b?.battery_kwh ?? variant.battery_kwh) ? `${b?.battery_kwh ?? variant.battery_kwh} kWh` : null,
    (b?.seats ?? variant.seats) ? `${b?.seats ?? variant.seats} seats` : null].filter(Boolean) as string[];
  const pill = (on: boolean) => cn("rounded-full border px-3.5 py-1.5 text-sm", on ? "border-accent bg-accent text-white" : "border-line text-mute hover:text-ink");

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-mute">{brandName} {modelName}</p>
          <h2 className="font-[family-name:var(--font-display)] text-2xl font-bold text-ink">{variant.name}</h2>
          <div className="mt-2 flex flex-wrap gap-1.5 text-xs">
            {chips.map((t) => <span key={t} className="rounded-full border border-line bg-panel-soft px-2.5 py-1 text-ink">{t}</span>)}
          </div>
        </div>
        <div className="inline-flex rounded-2xl border border-line bg-panel p-1 text-sm">
          {([["equipment", "Equipment"], ["specs", "Specifications"], ["guide", "Feature guide"]] as const).map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)}
              className={cn("rounded-xl px-3.5 py-1.5 font-semibold transition", tab === k ? "bg-accent text-white" : "text-mute hover:text-ink")}>{l}</button>
          ))}
        </div>
      </div>

      {isLoading && <Skeleton className="h-72 rounded-3xl" />}

      {!isLoading && !hasData && tab !== "guide" && (
        <div className="rounded-3xl border border-line bg-panel p-6">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-5 w-5 shrink-0 text-accent-2" />
            <div>
              <p className="font-semibold text-ink">{brandName}&apos;s spec sheet for this variant isn&apos;t loaded yet</p>
              <p className="mt-1 text-sm text-mute">
                We only show specifications and equipment exactly as {brandName} publishes them, so nothing here is estimated.
                Meanwhile, check the official page, or open the feature guide to see what common equipment means.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {data?.model_url && (
                  <a href={data.model_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white">
                    Official {brandName} {modelName} page <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
                <button onClick={() => setTab("guide")} className="inline-flex items-center gap-1.5 rounded-full border border-line px-4 py-2 text-sm text-ink hover:border-accent">
                  <BookOpen className="h-4 w-4" /> Feature guide
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {hasData && tab === "equipment" && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={() => setCat("all")} className={pill(cat === "all")}>All {known.length}</button>
            {CATS.map((c) => {
              const n = known.filter((f) => FEATURE_INFO[f.key].cat === c.id).length;
              return n ? <button key={c.id} onClick={() => setCat(c.id)} className={pill(cat === c.id)}>{c.label} {n}</button> : null;
            })}
            <div className="ml-auto flex items-center gap-2 rounded-full border border-line bg-panel px-3">
              <Search className="h-3.5 w-3.5 text-mute" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find a feature" className="h-8 w-40 bg-transparent text-sm text-ink placeholder:text-mute/70 focus:outline-none" />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {shown.map((f) => (
              <div key={f.key + f.label} className="overflow-hidden rounded-3xl border border-line bg-panel">
                {data?.photos?.[f.key]
                  ? <img src={imgSrc(data.photos[f.key].image_url, 640)} alt={f.label} loading="lazy" referrerPolicy="no-referrer" className="h-40 w-full bg-panel-soft object-cover" />
                  : <div className="grid h-40 place-items-center bg-panel-soft"><EquipmentArt k={f.key} className="h-28 w-44 text-ink/70" /></div>}
                <div className="p-4">
                  <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-good"><CheckCircle2 className="h-3.5 w-3.5" />Standard on this variant</p>
                  <p className="mt-1 font-semibold text-ink">{f.label}</p>
                  <p className="mt-1 text-sm text-mute">{FEATURE_INFO[f.key].what}</p>
                </div>
              </div>
            ))}
          </div>
          {shown.length === 0 && <p className="text-sm text-mute">No equipment matches this filter.</p>}
          {other.length > 0 && (
            <div className="rounded-3xl border border-line bg-panel p-5">
              <p className="font-semibold text-ink">Also listed by {brandName}</p>
              <ul className="mt-3 grid gap-x-6 gap-y-1.5 text-sm text-ink sm:grid-cols-2">
                {other.map((f) => <li key={f.label} className="flex gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-good" />{f.label}</li>)}
              </ul>
            </div>
          )}
        </>
      )}

      {hasData && tab === "specs" && (groups.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {groups.map(([g, rows]) => (
            <div key={g} className="rounded-3xl border border-line bg-panel p-5">
              <p className="font-semibold text-ink">{g}</p>
              <dl className="mt-3 divide-y divide-line text-sm">
                {rows.map((r) => (
                  <div key={r.key} className="flex justify-between gap-4 py-2"><dt className="text-mute">{r.label}</dt><dd className="text-right font-medium text-ink">{r.value}</dd></div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      ) : <p className="text-sm text-mute">{brandName} lists equipment for this variant but no technical specifications.</p>)}

      {tab === "guide" && (
        <>
          <p className="text-sm text-mute">Equipment {brandName} lists across the {modelName} range, with how many of its {mf?.total_variants ?? "…"} variants include each item. The Equipment tab shows exactly what this variant has.</p>
          {mf && mf.features.length === 0 && <p className="text-sm text-mute">{brandName}&apos;s equipment lists for the {modelName} aren&apos;t loaded yet.</p>}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(mf?.features ?? []).filter((f) => FEATURE_INFO[f.key] || f.photo).map((f) => (
              <div key={f.key} className="overflow-hidden rounded-3xl border border-line bg-panel">
                {f.photo
                  ? <img src={imgSrc(f.photo, 640)} alt={f.label} loading="lazy" referrerPolicy="no-referrer" className="h-36 w-full bg-panel-soft object-cover" />
                  : <div className="grid h-36 place-items-center bg-panel-soft"><EquipmentArt k={f.key} className="h-24 w-36 text-ink/60" /></div>}
                <div className="p-4 pt-3">
                  <p className="text-sm font-semibold text-ink">{f.label}</p>
                  {FEATURE_INFO[f.key] && <p className="mt-1 text-xs text-mute">{FEATURE_INFO[f.key].what}</p>}
                  <p className="mt-1.5 text-[11px] text-mute/80">On {f.variants} of {mf?.total_variants} variants</p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {hasData && source && (
        <p className="text-xs text-mute">
          From {brandName}&apos;s official specifications{asOf ? `, read ${ago(asOf)}` : ""} · <a href={source} target="_blank" rel="noreferrer" className="text-accent-2 hover:underline">source</a>.
          Feature photos are from the manufacturer's site for this model.
        </p>
      )}
    </div>
  );
}
