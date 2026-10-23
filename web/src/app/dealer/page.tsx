"use client";

import { useState } from "react";
import useSWR from "swr";
import { toast } from "sonner";
import { Building2, Send } from "lucide-react";
import { api, fetcher, type Account, type Brand } from "@/lib/api";
import { ago, inr } from "@/lib/format";
import { logout, SignedIn } from "@/components/signed-in";
import { Button, Card, Empty, Input, Label, SectionTitle, Select, Textarea } from "@/components/ui";

type Req = { id: number; dealer_id: string; dealer: string; variant: string; model: string; city: string; pincode: string | null; colour: string | null;
  finance: number; exchange: number; purchase_by: string | null; note: string | null; created: string; answered: number };
type Hit = { id: string; name: string; address: string; pincode: string | null; on_onroad: number };

function Claim() {
  const { data: brands } = useSWR<Brand[]>("/brands", fetcher);
  const [brand, setBrand] = useState("");
  const [text, setText] = useState("");
  const [designation, setDesignation] = useState("");
  const { data: hits } = useSWR<Hit[]>(brand ? `/dealers/search?brand=${brand}&text=${encodeURIComponent(text)}` : null, fetcher);
  async function claim(id: string) {
    if (!designation) return toast.error("Add your designation first");
    try { const r = await api<{ note: string }>("/dealer/claim", { method: "POST", body: JSON.stringify({ dealer_id: id, designation }) }); toast.success(r.note); }
    catch (e) { toast.error((e as Error).message); }
  }
  return (
    <Card className="p-6">
      <h3 className="flex items-center gap-2 text-lg text-white"><Building2 className="h-5 w-5 text-accent" />Claim your showroom</h3>
      <p className="mt-1 text-sm text-mute">Find your dealership (listed from the manufacturer&apos;s dealer locator). We verify every claim with the showroom&apos;s published phone or email.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Select value={brand} onChange={(e) => setBrand(e.target.value)}>
          <option value="">Brand</option>{(brands ?? []).map((b) => <option key={b.slug} value={b.slug}>{b.name}</option>)}
        </Select>
        <Input placeholder="Showroom name or area" value={text} onChange={(e) => setText(e.target.value)} />
        <Input placeholder="Your designation, e.g. Sales manager" value={designation} onChange={(e) => setDesignation(e.target.value)} />
      </div>
      <div className="mt-4 divide-y divide-line">
        {hits?.map((h) => (
          <div key={h.id} className="flex items-center gap-3 py-3">
            <div className="min-w-0 flex-1"><p className="text-white">{h.name}</p><p className="truncate text-xs text-mute">{h.address}</p></div>
            {h.on_onroad ? <span className="text-xs text-mute">Already on OnRoad</span> : <Button size="sm" variant="outline" onClick={() => claim(h.id)}>Claim</Button>}
          </div>
        ))}
      </div>
    </Card>
  );
}

function QuoteBox({ r, onDone }: { r: Req; onDone: () => void }) {
  const [v, setV] = useState({ ex_showroom_inr: "", road_tax_inr: "", registration_inr: "", insurance_inr: "", accessories_inr: "0", discount_inr: "0", waiting_weeks: "", note: "" });
  const [busy, setBusy] = useState(false);
  const num = (s: string) => Number(s.replace(/\D/g, "") || 0);
  const total = num(v.ex_showroom_inr) + num(v.road_tax_inr) + num(v.registration_inr) + num(v.insurance_inr) + num(v.accessories_inr) - num(v.discount_inr);
  async function send() {
    setBusy(true);
    try {
      await api("/dealer/quotes", { method: "POST", body: JSON.stringify({
        request_id: r.id, dealer_id: r.dealer_id, ex_showroom_inr: num(v.ex_showroom_inr), road_tax_inr: num(v.road_tax_inr),
        registration_inr: num(v.registration_inr), insurance_inr: num(v.insurance_inr), accessories_inr: num(v.accessories_inr),
        discount_inr: num(v.discount_inr), waiting_weeks: v.waiting_weeks ? num(v.waiting_weeks) : null, note: v.note || null }) });
      toast.success("Quote sent to the buyer"); onDone();
    } catch (e) { toast.error((e as Error).message); } finally { setBusy(false); }
  }
  const f = (k: keyof typeof v, label: string) => (
    <div><Label>{label}</Label><Input inputMode="numeric" value={v[k]} onChange={(e) => setV({ ...v, [k]: e.target.value })} /></div>
  );
  return (
    <div className="mt-4 space-y-3 rounded-2xl border border-line p-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {f("ex_showroom_inr", "Ex-showroom ₹")}{f("road_tax_inr", "Road tax ₹")}{f("registration_inr", "Registration ₹")}{f("insurance_inr", "Insurance ₹")}
        {f("accessories_inr", "Accessories ₹")}{f("discount_inr", "Discount ₹")}{f("waiting_weeks", "Waiting (weeks)")}
      </div>
      <Textarea rows={2} placeholder="Note to buyer (optional)" value={v.note} onChange={(e) => setV({ ...v, note: e.target.value })} />
      <div className="flex items-center justify-between"><p className="text-white">On-road total: <b>{inr(total)}</b></p>
        <Button onClick={send} loading={busy} disabled={!num(v.ex_showroom_inr)}><Send className="h-4 w-4" />Send quote</Button></div>
    </div>
  );
}

function Desk({ me }: { me: Account }) {
  const { data: reqs, mutate } = useSWR<Req[]>("/dealer/requests", fetcher);
  const [open, setOpen] = useState<number | null>(null);
  return (
    <main className="mx-auto max-w-6xl px-5 pt-28 pb-24">
      <div className="flex items-end justify-between gap-4">
        <SectionTitle eyebrow="Dealer desk" title={me.name} sub="Buyers near you asking for your best on-road price. Their contact is shared only when they choose you." />
        <Button variant="outline" size="sm" onClick={logout}>Log out</Button>
      </div>
      <div className="mt-10"><Claim /></div>
      <h2 className="mt-12 font-[family-name:var(--font-display)] text-2xl font-bold text-white">Open requests</h2>
      <div className="mt-5 space-y-4">
        {reqs?.length === 0 && <Empty title="No open requests">Once your showroom claim is approved, buyer requests for your brand in your city show up here.</Empty>}
        {reqs?.map((r) => (
          <Card key={`${r.id}-${r.dealer_id}`} className="p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-white">{r.model} · {r.variant}</p>
                <p className="text-sm text-mute">{r.city}{r.pincode ? ` ${r.pincode}` : ""} · {ago(r.created)}{r.colour ? ` · ${r.colour}` : ""}{r.finance ? " · needs loan" : ""}{r.exchange ? " · has exchange" : ""}</p>
              </div>
              {r.answered ? <span className="text-sm text-emerald-300">Quoted</span> : <Button size="sm" onClick={() => setOpen(open === r.id ? null : r.id)}>Quote</Button>}
            </div>
            {open === r.id && <QuoteBox r={r} onDone={() => { setOpen(null); mutate(); }} />}
          </Card>
        ))}
      </div>
    </main>
  );
}

export default function DealerPage() {
  return <SignedIn roles={["dealer"]} next="/dealer">{(me) => <Desk me={me} />}</SignedIn>;
}
