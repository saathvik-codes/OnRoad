"use client";

// From "I've picked my car" to driving it home: the steps, documents and statutory fees for the buyer's state.
// Fees come from /api/onroad/quick (the same state rules as every price on OnRoad); links go only to official portals.

import Link from "next/link";
import useSWR from "swr";
import { CheckCircle2, ExternalLink } from "lucide-react";
import { fetcher, type Breakdown } from "@/lib/api";
import { inr } from "@/lib/format";
import { useCity, withCity } from "@/components/city";
import { Card, SectionTitle } from "@/components/ui";

const STEPS: { t: string; d: string; docs?: string[]; link?: [string, string] }[] = [
  { t: "Compare the on-road price and get quotes", d: "Check the itemised on-road price for your city, then ask nearby showrooms for written quotes. Anything beyond road tax, registration, insurance, TCS and FASTag (handling, \"logistics\", forced accessories) is optional.",
    link: ["/calculator", "Check a dealer quote"] },
  { t: "Book the car", d: "Pay the booking amount against a receipt that names the exact variant, colour, price and expected delivery date. Ask how the booking is refunded if you cancel." },
  { t: "Arrange the loan (if any)", d: "Get the bank's sanction letter before you pay the balance. The car is registered with the bank's lien (hypothecation), which adds a small fee.",
    docs: ["PAN card", "Address proof", "Income proof (salary slips / ITR)", "Bank statements"] },
  { t: "Buy insurance", d: "Third-party cover for 3 years is mandatory for new cars (5 years for two-wheelers). Own-damage cover can be bought from any insurer, not only the dealer's. Compare at least two quotes." },
  { t: "Pay and collect the invoice", d: "The tax invoice carries the ex-showroom price with GST. TCS (1% above ₹10 lakh) is collected here and can be claimed back in your income-tax return." },
  { t: "Registration at the RTO", d: "The dealer usually files registration on the government's Vahan system. You pay road tax and registration fees; the car gets a registration number, and the RC is issued (smart card in most states).",
    docs: ["Form 20 (application)", "Form 21 (sale certificate from dealer)", "Form 22 (road-worthiness)", "Insurance certificate", "Address proof", "PAN or Form 60", "Form 34 if on loan"],
    link: ["https://vahan.parivahan.gov.in/vahanservice/", "Vahan citizen services"] },
  { t: "High-security number plates and FASTag", d: "HSRP plates are fitted by the dealer (their cost is included in the vehicle price for new vehicles). Link a FASTag to the registration number before highway driving." },
  { t: "Delivery inspection", d: "Before you sign the delivery note, check the VIN and engine number against the invoice, the manufacturing month, odometer, paint and panels, and that every promised accessory is there." },
];

export default function BuyingGuide() {
  const { city } = useCity();
  const { data: b } = useSWR<Breakdown>(withCity("/onroad/quick?ex_showroom=1000000&fuel=Petrol&engine_cc=1197", city), fetcher);
  const fee = (prefix: string) => b?.lines.find((l) => l.label.toLowerCase().startsWith(prefix));
  const rows = [fee("road tax"), fee("registration"), fee("road safety"), fee("insurance: third"), fee("fastag"), fee("tcs")].filter(Boolean);

  return (
    <main className="mx-auto max-w-5xl px-5 pb-24 pt-28">
      <SectionTitle eyebrow="Buying guide" title="From choosing your car to driving it home"
        sub={`Every step, the documents you need, and the statutory charges in ${b?.state_name ?? "your state"}.`} />

      <ol className="mt-10 space-y-4">
        {STEPS.map((s, i) => (
          <li key={s.t}>
            <Card className="p-5 sm:p-6">
              <div className="flex gap-4">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent font-semibold text-white">{i + 1}</span>
                <div className="min-w-0">
                  <p className="font-semibold text-ink">{s.t}</p>
                  <p className="mt-1 text-sm text-mute">{s.d}</p>
                  {s.docs && (
                    <ul className="mt-3 grid gap-1.5 text-sm text-ink sm:grid-cols-2">
                      {s.docs.map((d) => <li key={d} className="flex gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-good" />{d}</li>)}
                    </ul>
                  )}
                  {s.link && (s.link[0].startsWith("http")
                    ? <a href={s.link[0]} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-sm text-accent-2 hover:underline">{s.link[1]} <ExternalLink className="h-3.5 w-3.5" /></a>
                    : <Link href={s.link[0]} className="mt-3 inline-block text-sm text-accent hover:underline">{s.link[1]} →</Link>)}
                </div>
              </div>
            </Card>
          </li>
        ))}
      </ol>

      <Card className="mt-8 p-6">
        <p className="font-semibold text-ink">Statutory charges in {b?.state_name ?? city}, for a ₹10 lakh petrol car</p>
        <p className="mt-1 text-xs text-mute">From the same state rules used for every on-road price on OnRoad. Open any car for its exact numbers.</p>
        <dl className="mt-4 divide-y divide-line text-sm">
          {rows.map((l) => l && (
            <div key={l.label} className="flex justify-between gap-4 py-2.5">
              <dt className="text-mute">{l.label}<span className="block text-xs text-mute/80">{l.basis}</span></dt>
              <dd className="shrink-0 font-mono text-ink">{l.amount_inr != null ? inr(l.amount_inr) : "—"}</dd>
            </div>
          ))}
        </dl>
      </Card>

      <Card className="mt-8 p-6">
        <p className="font-semibold text-ink">Insurance, simply</p>
        <div className="mt-4 grid gap-6 text-sm sm:grid-cols-2">
          <div>
            <p className="font-medium text-ink">What&apos;s mandatory</p>
            <p className="mt-1 text-mute">Third-party cover: 3 years for a new car, 5 years for a new two-wheeler, at premiums fixed by IRDAI (shown in every on-road price here). It pays for damage you cause to others, not to your own vehicle.</p>
            <p className="mt-4 font-medium text-ink">Own-damage cover (optional, strongly advised)</p>
            <p className="mt-1 text-mute">Priced on the IDV (insured declared value, roughly the invoice price minus depreciation). Insurers compete on this part, so get two or three quotes. The dealer&apos;s policy is not compulsory.</p>
            <p className="mt-4 font-medium text-ink">No-claim bonus</p>
            <p className="mt-1 text-mute">Each claim-free year lowers the own-damage premium: 20%, then 25%, 35%, 45% and up to 50%. It belongs to you, not the car, so it transfers when you change vehicles.</p>
          </div>
          <div>
            <p className="font-medium text-ink">Add-ons worth knowing</p>
            <ul className="mt-1 space-y-1 text-mute">
              <li><b className="text-ink">Zero depreciation</b>: pays replaced parts without deducting depreciation.</li>
              <li><b className="text-ink">Engine protect</b>: covers engine damage from water ingress, which a standard policy excludes.</li>
              <li><b className="text-ink">Return to invoice</b>: pays the full invoice value if the car is stolen or written off.</li>
              <li><b className="text-ink">Roadside assistance</b>: towing, battery jump-start, flat tyre help.</li>
              <li><b className="text-ink">Personal accident cover</b>: ₹15 lakh for the owner-driver, compulsory unless you already hold one.</li>
            </ul>
            <p className="mt-4 font-medium text-ink">Making a claim</p>
            <ol className="mt-1 list-decimal space-y-1 pl-4 text-mute">
              <li>Inform the insurer immediately (app or helpline) and note the claim number.</li>
              <li>File a police report (FIR) for theft or third-party injury.</li>
              <li>Don&apos;t repair before the surveyor inspects the damage.</li>
              <li>Use a network garage for cashless repair, or pay and claim reimbursement with bills.</li>
            </ol>
            <p className="mt-3 text-mute">If a claim is unfairly rejected, complain to the insurer first, then on IRDAI&apos;s Bima Bharosa portal.</p>
            <div className="mt-2 flex flex-wrap gap-3">
              <a href="https://bimabharosa.irdai.gov.in" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent-2 hover:underline">Bima Bharosa (IRDAI) <ExternalLink className="h-3.5 w-3.5" /></a>
              <a href="https://irdai.gov.in" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent-2 hover:underline">IRDAI <ExternalLink className="h-3.5 w-3.5" /></a>
            </div>
          </div>
        </div>
      </Card>
    </main>
  );
}
