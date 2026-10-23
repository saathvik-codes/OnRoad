// OnRoad mark: a gradient "o" that is also a wheel / road loop, with a lane dash running through it,
// next to a clean lowercase wordmark (in the spirit of modern corporate wordmarks like amdocs, but our own design).

export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <defs>
        <linearGradient id="or-g" x1="6" y1="10" x2="58" y2="56" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#ffb347" />
          <stop offset="0.45" stopColor="#ff4d2e" />
          <stop offset="1" stopColor="#c2185b" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="22" fill="none" stroke="url(#or-g)" strokeWidth="11" />
      {/* road: a lane cut sweeping through the ring */}
      <path d="M6 44 C 22 34, 40 30, 60 18" fill="none" stroke="#05060a" strokeWidth="6" strokeLinecap="round" />
      <path d="M14 39.5 L 20 36.4 M 29 32.4 L 35 30 M 44 26.2 L 50 23.3" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ size = 30, className }: { size?: number; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className ?? ""}`}>
      <LogoMark size={size} />
      <span className="font-[family-name:var(--font-display)] text-[1.35rem] font-bold lowercase tracking-[-0.04em] text-white">
        on<span className="bg-gradient-to-r from-[#ffb347] via-[#ff4d2e] to-[#c2185b] bg-clip-text text-transparent">road</span>
      </span>
    </span>
  );
}
