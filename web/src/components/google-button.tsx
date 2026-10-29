"use client";

import { Track } from "@/lib/track";
import { useEffect, useRef, useState, useCallback } from "react";
import { api, type Account } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { cn } from "@/components/ui";

type Gsi = {
  accounts: {
    id: {
      initialize: (o: {
        client_id: string;
        callback: (r: { credential: string }) => void;
        ux_mode?: string;
        auto_select?: boolean;
      }) => void;
      renderButton: (el: HTMLElement, o: Record<string, unknown>) => void;
      prompt: (fn?: (notification: { isNotDisplayed: () => boolean; getNotDisplayedReason: () => string }) => void) => void;
    };
  };
};

interface GoogleButtonProps {
  onDone: (acc: Account) => void;
  onError: (msg: string) => void;
  dividerText?: string | null;
  className?: string;
}

/**
 * Pixel-perfect, native-styled Google Sign-In button for OnRoad.
 * Renders a crisp dark button matching OnRoad design system with official Google branding,
 * with Google Identity Services active behind a transparent overlay for 100% secure, seamless 1-tap auth.
 */
export function GoogleButton({
  onDone,
  onError,
  dividerText = "or with email",
  className,
}: GoogleButtonProps) {
  const boxRef = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleCredential = useCallback(async (credential: string) => {
    setLoading(true);
    try {
      Track.login("google");
      const acc = await api<Account>("/auth/google", {
        method: "POST",
        body: JSON.stringify({ id_token: credential }),
      });
      onDone(acc);
    } catch (e) {
      onError((e as Error).message || "Google sign-in failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [onDone, onError]);

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        const cfg = await api<{ client_id: string | null }>("/auth/google/config").catch(() => null);
        if (!cfg?.client_id || !alive) return;

        const w = window as unknown as { google?: Gsi };
        if (!w.google) {
          await new Promise<void>((res, rej) => {
            const existingScript = document.querySelector('script[src*="accounts.google.com/gsi/client"]');
            if (existingScript) {
              existingScript.addEventListener("load", () => res());
              return;
            }
            const s = document.createElement("script");
            s.src = "https://accounts.google.com/gsi/client";
            s.async = true;
            s.defer = true;
            s.onload = () => res();
            s.onerror = () => rej(new Error("Failed to load Google Identity Services"));
            document.head.appendChild(s);
          }).catch(() => null);
        }

        if (!alive || !w.google) return;

        w.google.accounts.id.initialize({
          client_id: cfg.client_id,
          callback: ({ credential }) => {
            handleCredential(credential);
          },
        });

        if (boxRef.current) {
          // Render the official GIS button inside our transparent overlay
          boxRef.current.innerHTML = "";
          w.google.accounts.id.renderButton(boxRef.current, {
            type: "standard",
            theme: "filled_black",
            size: "large",
            shape: "rectangular",
            width: 380,
            text: "continue_with",
            logo_alignment: "left",
          });
        }

        if (alive) {
          setReady(true);
        }
      } catch (err) {
        console.error("Google auth init error:", err);
      }
    })();

    return () => {
      alive = false;
    };
  }, [handleCredential]);

  const handleManualClick = () => {
    const w = window as unknown as { google?: Gsi };
    if (w.google?.accounts?.id) {
      setLoading(true);
      w.google.accounts.id.prompt((notification) => {
        setLoading(false);
        if (notification.isNotDisplayed()) {
          console.log("One tap prompt not displayed:", notification.getNotDisplayedReason());
        }
      });
    }
  };

  return (
    <div className={cn("w-full", className)}>
      {/* Outer button wrapper */}
      <div className="relative w-full h-11">
        {/* Visual Custom Dark Mode Google Button */}
        <button
          type="button"
          onClick={handleManualClick}
          disabled={loading}
          className="w-full h-full rounded-xl border border-line bg-panel-soft/80 hover:bg-panel-soft hover:border-white/20 active:scale-[0.99] transition-all duration-150 flex items-center justify-center gap-3 px-4 text-sm font-medium text-ink shadow-xs select-none"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin text-accent" />
          ) : (
            <svg className="h-4.5 w-4.5 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
          )}
          <span className="font-medium text-ink text-sm">
            {loading ? "Connecting to Google..." : "Continue with Google"}
          </span>
        </button>

        {/* Transparent Official Google Click Overlay */}
        {ready && (
          <div
            ref={boxRef}
            aria-hidden="true"
            className="absolute inset-0 w-full h-full overflow-hidden rounded-xl opacity-[0.001] cursor-pointer z-10 flex items-center justify-center [&_iframe]:w-full [&_iframe]:h-full [&_iframe]:scale-125 [&_iframe]:cursor-pointer pointer-events-auto"
            style={{ colorScheme: "light" }}
          />
        )}
      </div>

      {dividerText && (
        <div className="mt-5 flex items-center gap-3 text-xs text-mute">
          <span className="h-px flex-1 bg-line" />
          <span>{dividerText}</span>
          <span className="h-px flex-1 bg-line" />
        </div>
      )}
    </div>
  );
}
