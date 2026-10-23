"use client";

import useSWR from "swr";
import { toast } from "sonner";
import { api, fetcher } from "@/lib/api";
import { ago } from "@/lib/format";
import { logout, SignedIn } from "@/components/signed-in";
import { Button, Card, Empty, Pill, SectionTitle } from "@/components/ui";

type Item = { id: number; dealer_id: string; channel: string; recipient: string; subject: string; body: string; status: string; created: string };

function Admin() {
  const { data: claims, mutate: reClaims } = useSWR<Item[]>("/admin/claims", fetcher);
  const { data: outreach, mutate: reOut } = useSWR<Item[]>("/admin/outreach", fetcher);
  const act = async (path: string, done: () => void) => {
    try { const r = await api<{ note?: string }>(path, { method: "POST" }); toast.success(r.note ?? "Done"); done(); }
    catch (e) { toast.error((e as Error).message); }
  };
  return (
    <main className="mx-auto max-w-6xl px-5 pt-28 pb-24">
      <div className="flex items-end justify-between gap-4">
        <SectionTitle eyebrow="Admin" title="Approvals" sub="Nothing is sent to a dealer and no showroom access is granted until you approve it here." />
        <Button variant="outline" size="sm" onClick={logout}>Log out</Button>
      </div>
      <h2 className="mt-12 font-[family-name:var(--font-display)] text-2xl font-bold text-white">Showroom claims</h2>
      <div className="mt-5 space-y-3">
        {claims?.length === 0 && <Empty title="No pending claims" />}
        {claims?.map((c) => (
          <Card key={c.id} className="flex flex-wrap items-center gap-4 p-5">
            <div className="min-w-0 flex-1"><p className="text-white">{c.subject}</p><p className="text-sm text-mute">{c.body} · {c.recipient} · {ago(c.created)}</p></div>
            <Button size="sm" onClick={() => act(`/admin/claims/${c.id}/approve`, reClaims)}>Approve after verifying</Button>
          </Card>
        ))}
      </div>
      <h2 className="mt-12 font-[family-name:var(--font-display)] text-2xl font-bold text-white">Dealer outreach drafts</h2>
      <div className="mt-5 space-y-3">
        {outreach?.length === 0 && <Empty title="No drafts" />}
        {outreach?.map((o) => (
          <Card key={o.id} className="p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-white">{o.subject}</p>
              <div className="flex items-center gap-2"><Pill>{o.channel}</Pill><Pill>{o.status}</Pill>
                {o.status === "draft" && <Button size="sm" onClick={() => act(`/admin/outreach/${o.id}/approve`, reOut)}>Approve</Button>}</div>
            </div>
            <p className="mt-1 text-sm text-mute">To {o.recipient}</p>
            <pre className="mt-3 whitespace-pre-wrap font-sans text-sm text-white/80">{o.body}</pre>
          </Card>
        ))}
      </div>
    </main>
  );
}

export default function AdminPage() {
  return <SignedIn roles={["admin"]} next="/admin">{() => <Admin />}</SignedIn>;
}
