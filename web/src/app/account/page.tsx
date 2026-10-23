"use client";

import Link from "next/link";
import useSWR from "swr";
import { toast } from "sonner";
import { Award, MapPin, Phone, Trash2, TrendingDown, TrendingUp } from "lucide-react";
import { api, fetcher, type Account } from "@/lib/api";
import { ago, inr, lakh } from "@/lib/format";
import { logout, SignedIn } from "@/components/signed-in";
import { Button, Card, Empty, Pill, SectionTitle } from "@/components/ui";

type Saved = { variant_id: string; city: string; target_inr: number | null; variant: string; model: string; model_id: string; brand: string;
  current_inr: number | null; change_inr: number };
type Quote = { id: number; dealer: string; address: string; phone: string | null; on_road_inr: number; discount_inr: number;
  waiting_weeks: number | null; valid_until: string | null; note: string | null; created: string };
type Req = { id: number; variant: string; model: string; brand: string; city: string; created: string; status: string;
  fair_onroad_inr: number | null; quotes: Quote[] };

function Garage({ me }: { me: Account }) {
  const { data: saved, mutate: reSaved } = useSWR<Saved[]>("/me/saved", fetcher);
  const { data: reqs } = useSWR<Req[]>("/me/quotes", fetcher);

  async function remove(s: Saved) {
    try { await api(`/me/saved?variant_id=${encodeURIComponent(s.variant_id)}&city=${s.city}`, { method: "DELETE" }); reSaved(); }
    catch (e) { toast.error((e as Error).message); }
  }

  return (
    <main className="mx-auto max-w-6xl px-5 pt-28 pb-24">
      <div className="flex items-end justify-between gap-4">
        <SectionTitle eyebrow="My garage" title={`Hi ${me.name.split(" ")[0]}`} sub="Your quote requests with every dealer's answer ranked by real on-road price, and the cars you're watching." />
        <Button variant="outline" size="sm" onClick={logout}>Log out</Button>
      </div>

      <h2 className="mt-12 font-[family-name:var(--font-display)] text-2xl font-bold text-white">Dealer quotes</h2>
      <div className="mt-5 space-y-5">
        {reqs?.length === 0 && <Empty title="No quote requests yet">Open any car, choose a variant and tap “Get dealer quotes”.</Empty>}
        {reqs?.map((r) => (
          <Card key={r.id} className="p-6">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-lg text-white">{r.brand} {r.model} <span className="text-mute">· {r.variant}</span></p>
              <p className="text-sm text-mute">{r.city} · asked {ago(r.created)}</p>
            </div>
            {r.fair_onroad_inr && <p className="mt-1 text-sm text-mute">Fair statutory on-road price: <span className="text-white">{inr(r.fair_onroad_inr)}</span></p>}
            {r.quotes.length === 0 ? <p className="mt-4 text-sm text-mute">Waiting for dealers. Showrooms on OnRoad usually answer within a day.</p> : (
              <div className="mt-4 divide-y divide-line">
                {r.quotes.map((q, i) => (
                  <div key={q.id} className="flex flex-wrap items-center gap-4 py-3">
                    {i === 0 ? <Pill className="border-emerald-400/40 text-emerald-300"><Award className="h-3 w-3" />Best price</Pill> : <span className="w-[86px]" />}
                    <div className="min-w-0 flex-1">
                      <p className="text-white">{q.dealer}</p>
                      <p className="flex items-center gap-1 truncate text-xs text-mute"><MapPin className="h-3 w-3" />{q.address}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold text-white">{inr(q.on_road_inr)}</p>
                      <p className="text-xs text-mute">{q.discount_inr ? `incl. ${inr(q.discount_inr)} off · ` : ""}{q.waiting_weeks != null ? `${q.waiting_weeks} wk wait` : ""}</p>
                    </div>
                    {q.phone && <a href={`tel:${q.phone}`}><Button size="sm" variant="outline"><Phone className="h-3.5 w-3.5" />Call</Button></a>}
                  </div>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>

      <h2 className="mt-14 font-[family-name:var(--font-display)] text-2xl font-bold text-white">Watching</h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {saved?.length === 0 && <Empty title="Nothing saved">Tap the heart on a variant to watch its price.</Empty>}
        {saved?.map((s) => (
          <Card key={s.variant_id + s.city} className="p-5">
            <Link href={`/cars/${s.model_id}`} className="text-white hover:text-accent">{s.brand} {s.model}</Link>
            <p className="text-sm text-mute">{s.variant}</p>
            <div className="mt-3 flex items-end justify-between">
              <div>
                <p className="text-xl font-bold text-white">{lakh(s.current_inr)}</p>
                {s.change_inr !== 0 && (
                  <p className={`flex items-center gap-1 text-xs ${s.change_inr < 0 ? "text-emerald-300" : "text-amber-300"}`}>
                    {s.change_inr < 0 ? <TrendingDown className="h-3 w-3" /> : <TrendingUp className="h-3 w-3" />}{inr(Math.abs(s.change_inr))} since last change
                  </p>
                )}
              </div>
              <button onClick={() => remove(s)} aria-label="Stop watching" className="text-mute hover:text-white"><Trash2 className="h-4 w-4" /></button>
            </div>
          </Card>
        ))}
      </div>
    </main>
  );
}

export default function AccountPage() {
  return <SignedIn roles={["buyer", "admin"]} next="/account">{(me) => <Garage me={me} />}</SignedIn>;
}
