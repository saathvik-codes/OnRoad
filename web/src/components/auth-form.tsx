"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { mutate } from "swr";
import { api, type Account } from "@/lib/api";
import { Logo } from "@/components/logo";
import { Button, Card, Input, Label } from "@/components/ui";

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const sp = useSearchParams();
  const [role, setRole] = useState<"buyer" | "dealer">(sp.get("role") === "dealer" ? "dealer" : "buyer");
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const body = mode === "login" ? { email: form.email, password: form.password } : { ...form, phone: form.phone || null, role };
      const acc = await api<Account>(`/auth/${mode}`, { method: "POST", body: JSON.stringify(body) });
      await mutate("/auth/me", acc, false);
      toast.success(mode === "login" ? `Welcome back, ${acc.name.split(" ")[0]}` : "Account created");
      router.push(sp.get("next") ?? (acc.role === "dealer" ? "/dealer" : acc.role === "admin" ? "/admin" : "/account"));
    } catch (err) { toast.error((err as Error).message); } finally { setBusy(false); }
  }

  return (
    <main className="relative grid min-h-screen place-items-center px-5 py-28">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_30%,rgba(255,77,46,0.16),transparent_70%)]" />
      <Card className="relative w-full max-w-md p-8">
        <Logo size={34} />
        <h1 className="mt-6 font-[family-name:var(--font-display)] text-3xl font-bold text-white">
          {mode === "login" ? "Log in" : role === "dealer" ? "List your showroom" : "Create your garage"}
        </h1>
        <p className="mt-1 text-sm text-mute">
          {mode === "login" ? "Saved cars, dealer quotes and price alerts." : role === "dealer"
            ? "Answer buyer requests with your best on-road price and post your offers."
            : "Save cars, watch prices and let dealers compete for your purchase."}
        </p>
        {mode === "signup" && (
          <div className="mt-6 flex rounded-full border border-line p-1 text-sm">
            {(["buyer", "dealer"] as const).map((r) => (
              <button type="button" key={r} onClick={() => setRole(r)} className={`flex-1 rounded-full py-2 ${role === r ? "bg-white text-black" : "text-mute"}`}>
                {r === "buyer" ? "I'm buying" : "I'm a dealer"}
              </button>
            ))}
          </div>
        )}
        <form onSubmit={submit} className="mt-6 space-y-4">
          {mode === "signup" && <div><Label>Full name</Label><Input required value={form.name} onChange={set("name")} /></div>}
          <div><Label>Email</Label><Input required type="email" value={form.email} onChange={set("email")} autoComplete="email" /></div>
          {mode === "signup" && <div><Label hint="(optional)">Phone</Label><Input value={form.phone} onChange={set("phone")} inputMode="tel" /></div>}
          <div><Label hint={mode === "signup" ? "(8+ characters)" : undefined}>Password</Label>
            <Input required type="password" minLength={mode === "signup" ? 8 : undefined} value={form.password} onChange={set("password")}
              autoComplete={mode === "login" ? "current-password" : "new-password"} /></div>
          <Button type="submit" size="lg" loading={busy} className="w-full">{mode === "login" ? "Log in" : "Create account"}</Button>
        </form>
        <p className="mt-5 text-center text-sm text-mute">
          {mode === "login" ? <>New here? <Link href="/signup" className="text-accent">Create an account</Link></>
            : <>Have an account? <Link href="/login" className="text-accent">Log in</Link></>}
        </p>
      </Card>
    </main>
  );
}
