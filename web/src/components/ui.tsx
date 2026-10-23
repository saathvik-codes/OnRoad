"use client";

import clsx from "clsx";
import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

export const cn = (...c: Parameters<typeof clsx>) => clsx(...c);

export function Button({ variant = "primary", size = "md", loading, className, children, disabled, ...rest }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "outline"; size?: "sm" | "md" | "lg"; loading?: boolean }) {
  return (
    <button {...rest} disabled={disabled || loading}
      className={cn("inline-flex items-center justify-center gap-2 rounded-full font-medium transition disabled:opacity-50 cursor-pointer",
        size === "sm" && "h-8 px-3.5 text-sm", size === "md" && "h-10 px-5 text-sm", size === "lg" && "h-12 px-7 text-base",
        variant === "primary" && "bg-accent text-white shadow-[0_0_30px_-6px_rgba(255,77,46,0.7)] hover:brightness-110",
        variant === "outline" && "border border-line bg-panel text-ink hover:border-line/80 hover:bg-panel-soft",
        variant === "ghost" && "text-mute hover:bg-panel-soft hover:text-ink", className)}>
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}

const field = "w-full rounded-xl border border-line bg-panel px-3.5 text-sm text-ink placeholder:text-mute/60 focus:border-accent/70 focus:outline-none focus:ring-2 focus:ring-accent/20";
export const Input = (p: InputHTMLAttributes<HTMLInputElement>) => <input {...p} className={cn(field, "h-11", p.className)} />;
export const Textarea = (p: TextareaHTMLAttributes<HTMLTextAreaElement>) => <textarea {...p} className={cn(field, "py-2.5", p.className)} />;
export const Select = (p: SelectHTMLAttributes<HTMLSelectElement>) => <select {...p} className={cn(field, "h-11", p.className)} />;

export function Label({ children, hint }: { children: ReactNode; hint?: string }) {
  return <label className="mb-1.5 block text-sm text-ink font-medium">{children}{hint && <span className="ml-1 text-mute font-normal">{hint}</span>}</label>;
}

export function Card({ className, children, id }: { className?: string; children: ReactNode; id?: string }) {
  return <div id={id} className={cn("rounded-2xl border border-line bg-panel shadow-sm", className)}>{children}</div>;
}

export function Pill({ className, children }: { className?: string; children: ReactNode }) {
  return <span className={cn("inline-flex items-center gap-1.5 rounded-full border border-line bg-panel-soft px-3 py-1 text-xs font-semibold text-ink shadow-xs", className)}>{children}</span>;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-xl bg-panel-soft border border-line/40", className)} />;
}

export function SectionTitle({ eyebrow, title, sub }: { eyebrow?: string; title: ReactNode; sub?: ReactNode }) {
  return (
    <div className="mb-10 max-w-3xl">
      {eyebrow && <p className="mb-3 text-xs font-semibold uppercase tracking-[0.25em] text-accent">{eyebrow}</p>}
      <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-ink sm:text-5xl">{title}</h2>
      {sub && <p className="mt-4 text-base text-mute sm:text-lg">{sub}</p>}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-panel/50 px-6 py-14 text-center">
      <p className="font-semibold text-ink">{title}</p>
      {children && <div className="mx-auto mt-2 max-w-md text-sm text-mute">{children}</div>}
    </div>
  );
}
