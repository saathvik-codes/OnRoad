"use client";

// Light / dark theme. THEME_SCRIPT (in <head>) applies the saved theme before first paint, so there is no flash and
// no hydration mismatch; components read it through a tiny external store.

import { useSyncExternalStore, type ReactNode } from "react";
import { Moon, Sun } from "lucide-react";

type Theme = "dark" | "light";
const KEY = "onroad_theme";

/** Runs before React: reads the saved choice (default dark) and sets html.dark / html.light + data-theme. */
export const THEME_SCRIPT = `(function(){try{var t=localStorage.getItem("${KEY}");if(t!=="light"&&t!=="dark")t="dark";var r=document.documentElement;r.classList.remove("light","dark");r.classList.add(t);r.setAttribute("data-theme",t);r.style.colorScheme=t;}catch(e){document.documentElement.classList.add("dark");}})();`;

const listeners = new Set<() => void>();
const read = (): Theme => (typeof document !== "undefined" && document.documentElement.classList.contains("light") ? "light" : "dark");
const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };

function apply(t: Theme) {
  const r = document.documentElement;
  r.classList.remove("light", "dark");
  r.classList.add(t);
  r.setAttribute("data-theme", t);
  r.style.colorScheme = t;
  try { localStorage.setItem(KEY, t); } catch { /* storage blocked */ }
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", t === "light" ? "#f8fafc" : "#05060a");
  listeners.forEach((fn) => fn());
}

/** Kept so existing imports keep working; the theme lives on <html>, not in React state. */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, read, () => "dark" as Theme);
  return { theme, setTheme: apply, toggleTheme: () => apply(read() === "dark" ? "light" : "dark") };
}

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  return (
    <button type="button" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className={`relative inline-flex h-9 w-9 items-center justify-center rounded-xl border border-line bg-panel-soft text-mute transition hover:text-ink ${className ?? ""}`}>
      {theme === "dark"
        ? <Sun className="h-4 w-4 text-amber-400 transition-transform duration-300 hover:rotate-45" />
        : <Moon className="h-4 w-4 text-indigo-500 transition-transform duration-300 hover:-rotate-12" />}
    </button>
  );
}
