"use client";

import Link from "next/link";
import useSWR, { mutate } from "swr";
import { api, fetcher, type Account } from "@/lib/api";
import { Button, Card, Skeleton } from "@/components/ui";

/** Renders children only for a signed-in account with one of the given roles. */
export function SignedIn({ roles, next, children }: { roles: Account["role"][]; next: string; children: (me: Account) => React.ReactNode }) {
  const { data: me, error, isLoading } = useSWR<Account>("/auth/me", fetcher, { shouldRetryOnError: false });
  if (isLoading) return <main className="mx-auto max-w-6xl px-5 pt-28"><Skeleton className="h-96" /></main>;
  if (error || !me) return (
    <main className="mx-auto grid min-h-[70vh] max-w-md place-items-center px-5 pt-28">
      <Card className="p-8 text-center">
        <p className="text-white">Please log in to continue.</p>
        <Link href={`/login?next=${encodeURIComponent(next)}`}><Button className="mt-5">Log in</Button></Link>
      </Card>
    </main>
  );
  if (!roles.includes(me.role)) return (
    <main className="mx-auto max-w-md px-5 pt-32 text-center text-mute">This page is for {roles.join(" / ")} accounts.</main>
  );
  return <>{children(me)}</>;
}

export async function logout() {
  await api("/auth/logout", { method: "POST" });
  await mutate("/auth/me", undefined, false);
  location.href = "/";
}
