"use client";

import { useEffect, useRef, useState } from "react";
import { api, type Account } from "@/lib/api";

type Gsi = {
  accounts: { id: {
    initialize: (o: { client_id: string; callback: (r: { credential: string }) => void; ux_mode?: string }) => void;
    renderButton: (el: HTMLElement, o: Record<string, unknown>) => void;
  } };
};

/** "Continue with Google" (Google Identity Services). The ID token goes to /api/auth/google, which verifies it with Google. */
export function GoogleButton({ onDone, onError }: { onDone: (acc: Account) => void; onError: (msg: string) => void }) {
  const box = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      const cfg = await api<{ client_id: string | null }>("/auth/google/config").catch(() => null);
      if (!cfg?.client_id || !alive) return;
      const w = window as unknown as { google?: Gsi };
      if (!w.google) {
        await new Promise<void>((res, rej) => {
          const s = document.createElement("script");
          s.src = "https://accounts.google.com/gsi/client"; s.async = true;
          s.onload = () => res(); s.onerror = () => rej(new Error("gsi"));
          document.head.appendChild(s);
        }).catch(() => null);
      }
      if (!alive || !w.google || !box.current) return;
      w.google.accounts.id.initialize({
        client_id: cfg.client_id,
        callback: async ({ credential }) => {
          try { onDone(await api<Account>("/auth/google", { method: "POST", body: JSON.stringify({ id_token: credential }) })); }
          catch (e) { onError((e as Error).message); }
        },
      });
      w.google.accounts.id.renderButton(box.current, { theme: "filled_black", size: "large", shape: "pill", text: "continue_with", width: 320 });
      setReady(true);
    })();
    return () => { alive = false; };
  }, [onDone, onError]);

  return (
    <div className={ready ? "mt-6" : "hidden"}>
      <div ref={box} className="flex justify-center" />
      <div className="mt-5 flex items-center gap-3 text-xs text-mute"><span className="h-px flex-1 bg-line" />or with email<span className="h-px flex-1 bg-line" /></div>
    </div>
  );
}
