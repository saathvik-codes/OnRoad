import { ImageResponse } from "next/og";

export const size = {
  width: 64,
  height: 64,
};
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#05060a",
          borderRadius: "16px",
        }}
      >
        <svg width="52" height="52" viewBox="0 0 64 64">
          <defs>
            <linearGradient id="or-g" x1="6" y1="10" x2="58" y2="56" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#ffb347" />
              <stop offset="45%" stopColor="#ff4d2e" />
              <stop offset="100%" stopColor="#c2185b" />
            </linearGradient>
          </defs>
          <circle cx="32" cy="32" r="22" fill="none" stroke="url(#or-g)" strokeWidth="11" />
          <path d="M6 44 C 22 34, 40 30, 60 18" fill="none" stroke="#05060a" strokeWidth="6" strokeLinecap="round" />
          <path d="M14 39.5 L 20 36.4 M 29 32.4 L 35 30 M 44 26.2 L 50 23.3" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      </div>
    ),
    {
      ...size,
    }
  );
}
