// Explanatory illustrations for car / two-wheeler equipment (drawn for OnRoad, theme-aware).
// They show WHAT a feature is, not a specific car, and are shown only for equipment the manufacturer lists on a variant.

import type { ReactNode } from "react";

const A = "var(--color-accent)";        // highlight colour
const B = "var(--color-accent-2)";      // secondary highlight

/** Shared side-profile car outline (viewBox 0 0 120 72). */
const CarSide = ({ o = 1 }: { o?: number }) => (
  <g opacity={o}>
    <path d="M10 50 L14 50 M30 50 L86 50 M102 50 L110 50 L110 41 L101 37 L86 25 L46 25 L33 36 L12 39 Z" />
    <circle cx="22" cy="50" r="7" /><circle cx="94" cy="50" r="7" />
    <path d="M48 28 L58 28 L58 36 L38 36 Z M62 28 L84 28 L94 36 L62 36 Z" opacity=".55" />
  </g>
);
/** Top view of a car (viewBox 0 0 120 72). */
const CarTop = () => (
  <g>
    <rect x="38" y="10" width="44" height="52" rx="12" />
    <path d="M44 22 Q60 16 76 22 L74 30 L46 30 Z M46 46 L74 46 L76 54 Q60 58 44 54 Z" opacity=".55" />
  </g>
);
/** Dashboard silhouette (viewBox 0 0 120 72). */
const Dash = () => (
  <g>
    <path d="M6 56 Q60 30 114 56" /><path d="M6 56 L6 66 L114 66 L114 56" opacity=".5" />
    <circle cx="36" cy="58" r="9" /><path d="M36 58 L41 53" />
  </g>
);

const ART: Record<string, ReactNode> = {
  // ── safety ─────────────────────────────────────────────────────────────────────────────
  airbags_6: (<g><CarTop /><g fill={A} stroke="none" opacity=".85">
    <ellipse cx="50" cy="24" rx="6" ry="5" /><ellipse cx="70" cy="24" rx="6" ry="5" />
    <rect x="34" y="20" width="4" height="34" rx="2" /><rect x="82" y="20" width="4" height="34" rx="2" />
    <ellipse cx="44" cy="40" rx="3" ry="5" /><ellipse cx="76" cy="40" rx="3" ry="5" /></g></g>),
  airbags_2: (<g><CarTop /><g fill={A} stroke="none" opacity=".85"><ellipse cx="50" cy="24" rx="6" ry="5" /><ellipse cx="70" cy="24" rx="6" ry="5" /></g></g>),
  esc: (<g><path d="M20 60 Q40 20 60 36 T100 14" stroke={A} strokeDasharray="4 4" /><g transform="translate(52 22) rotate(-25)"><rect x="-10" y="-6" width="20" height="12" rx="4" /></g>
    <path d="M70 52 a14 14 0 1 1 -1 0" stroke={B} /><path d="M66 50 l4 3 l-1 -5" stroke={B} /></g>),
  hill_hold: (<g><path d="M6 66 L114 26" /><g transform="translate(50 40) rotate(-20)"><CarSide /></g><path d="M20 56 l10 -4" stroke={A} strokeWidth="3" /></g>),
  tpms: (<g><circle cx="44" cy="38" r="22" /><circle cx="44" cy="38" r="12" /><path d="M78 20 h28 v24 h-28 z" stroke={B} />
    <path d="M84 36 h16 M92 26 v14" stroke={B} /><path d="M66 38 h12" stroke={A} strokeDasharray="2 3" /></g>),
  isofix: (<g><path d="M30 14 L40 54 L92 54" /><path d="M40 54 L36 66 M92 54 L96 66" opacity=".5" /><rect x="52" y="26" width="30" height="24" rx="8" stroke={A} />
    <path d="M56 54 v6 M78 54 v6" stroke={A} strokeWidth="3" /></g>),
  rear_parking_sensors: (<g><CarSide /><g stroke={A}><path d="M114 30 a12 12 0 0 1 0 22" /><path d="M118 24 a18 18 0 0 1 0 34" opacity=".6" /></g></g>),
  front_parking_sensors: (<g><g transform="translate(120 0) scale(-1 1)"><CarSide /></g><g stroke={A}><path d="M6 30 a12 12 0 0 0 0 22" /></g></g>),
  rear_camera: (<g><CarSide /><path d="M108 38 L120 28 M108 38 L120 50" stroke={A} /><circle cx="106" cy="38" r="2.5" fill={A} stroke="none" /></g>),
  camera_360: (<g><CarTop /><g stroke={A} opacity=".9"><path d="M60 8 L44 0 M60 8 L76 0" /><path d="M60 64 L44 72 M60 64 L76 72" />
    <path d="M36 36 L22 26 M36 36 L22 46" /><path d="M84 36 L98 26 M84 36 L98 46" /></g>
    <circle cx="60" cy="36" r="30" stroke={B} strokeDasharray="3 4" opacity=".7" /></g>),
  adas: (<g><CarSide o={0.9} /><path d="M110 40 L120 30 M110 40 L120 50" stroke={A} />
    <path d="M2 30 Q-2 40 2 50" stroke={B} /><g stroke={A} strokeDasharray="3 3"><path d="M30 64 L10 64" /><path d="M110 64 L90 64" /></g>
    <text x="40" y="18" fontSize="9" fill={A} stroke="none" fontWeight="700">L2</text></g>),
  blind_spot_monitor: (<g><CarTop /><path d="M86 30 L112 18 L112 54 Z" stroke={A} fill={A} fillOpacity=".12" /><path d="M34 30 L8 18 L8 54 Z" stroke={A} fill={A} fillOpacity=".12" /></g>),
  rear_disc_brakes: (<g><circle cx="60" cy="38" r="26" /><circle cx="60" cy="38" r="6" />{[0, 60, 120, 180, 240, 300].map((d) => (
    <circle key={d} cx={60 + 16 * Math.cos((d * Math.PI) / 180)} cy={38 + 16 * Math.sin((d * Math.PI) / 180)} r="2" />))}
    <path d="M78 14 Q92 38 78 62" stroke={A} strokeWidth="5" /></g>),
  front_disc: (<g><circle cx="60" cy="38" r="26" /><circle cx="60" cy="38" r="6" /><path d="M78 14 Q92 38 78 62" stroke={A} strokeWidth="5" /></g>),
  auto_headlamps: (<g><CarSide /><path d="M8 40 L-6 34 M8 42 L-6 42 M8 44 L-6 50" stroke={A} /><path d="M90 6 a8 8 0 1 0 10 10 a6 6 0 1 1 -10 -10" stroke={B} /></g>),
  rain_sensing_wipers: (<g><path d="M14 60 Q60 10 106 60" /><path d="M40 58 L62 26 M74 58 L92 34" stroke={A} />{[[30, 20], [52, 14], [80, 18], [96, 26]].map(([x, y]) => (
    <path key={x} d={`M${x} ${y} q3 5 0 7 q-3 -2 0 -7`} stroke={B} />))}</g>),
  electric_parking_brake: (<g><rect x="34" y="18" width="52" height="36" rx="10" /><text x="60" y="44" textAnchor="middle" fontSize="18" fontWeight="800" fill={A} stroke="none">P</text>
    <circle cx="60" cy="37" r="14" stroke={A} /></g>),

  // ── tech ──────────────────────────────────────────────────────────────────────────────
  touchscreen: (<g><Dash /><rect x="50" y="10" width="44" height="30" rx="4" stroke={A} /><path d="M58 30 l8 -8 l6 6 l10 -10" stroke={B} /><circle cx="86" cy="18" r="2" fill={A} stroke="none" /></g>),
  digital_cluster: (<g><rect x="12" y="16" width="96" height="40" rx="8" /><circle cx="38" cy="36" r="13" stroke={A} /><path d="M38 36 L46 28" stroke={A} />
    <circle cx="82" cy="36" r="13" stroke={B} /><text x="60" y="40" textAnchor="middle" fontSize="9" fill="currentColor" stroke="none">88</text></g>),
  android_auto_carplay: (<g><Dash /><rect x="46" y="10" width="48" height="30" rx="4" /><rect x="14" y="14" width="18" height="30" rx="4" stroke={B} />
    <path d="M32 28 Q40 28 46 26" stroke={A} strokeDasharray="2 2" /><g fill={A} stroke="none"><rect x="52" y="16" width="8" height="8" rx="2" /><rect x="64" y="16" width="8" height="8" rx="2" /><rect x="76" y="16" width="8" height="8" rx="2" /></g></g>),
  wireless_android_auto_carplay: (<g><Dash /><rect x="46" y="10" width="48" height="30" rx="4" /><rect x="14" y="14" width="18" height="30" rx="4" stroke={B} />
    <g stroke={A}><path d="M34 22 a6 6 0 0 1 8 0" /><path d="M32 18 a10 10 0 0 1 12 0" /></g>
    <g fill={A} stroke="none"><rect x="52" y="16" width="8" height="8" rx="2" /><rect x="64" y="16" width="8" height="8" rx="2" /><rect x="76" y="16" width="8" height="8" rx="2" /></g></g>),
  connected_car: (<g><CarSide /><rect x="86" y="2" width="16" height="26" rx="3" stroke={B} /><g stroke={A}><path d="M70 14 a10 10 0 0 1 12 0" /><path d="M66 9 a16 16 0 0 1 20 0" /></g></g>),
  wireless_charger: (<g><rect x="30" y="40" width="60" height="22" rx="6" /><rect x="44" y="10" width="32" height="44" rx="5" stroke={B} />
    <path d="M60 24 l-5 9 h7 l-5 9" stroke={A} strokeWidth="2.5" /></g>),
  premium_audio: (<g><circle cx="36" cy="38" r="22" /><circle cx="36" cy="38" r="9" stroke={A} /><circle cx="36" cy="38" r="3" fill={A} stroke="none" />
    <g stroke={B}><path d="M70 28 a14 14 0 0 1 0 20" /><path d="M80 20 a24 24 0 0 1 0 36" /><path d="M90 12 a34 34 0 0 1 0 52" opacity=".6" /></g></g>),
  hud: (<g><path d="M10 64 Q60 44 110 64" /><path d="M20 8 L100 8 L94 44 L26 44 Z" opacity=".6" /><text x="60" y="30" textAnchor="middle" fontSize="13" fontWeight="800" fill={A} stroke="none">60</text>
    <path d="M60 48 L60 38" stroke={B} strokeDasharray="2 2" /></g>),
  cruise_control: (<g><circle cx="60" cy="38" r="28" /><circle cx="60" cy="38" r="8" /><path d="M60 10 v20 M32 38 h20 M88 38 h-20" />
    <path d="M86 12 a36 36 0 0 1 10 22" stroke={A} /><path d="M92 30 l4 4 l3 -6" stroke={A} /></g>),
  keyless_entry: (<g><rect x="16" y="20" width="26" height="40" rx="10" /><circle cx="29" cy="34" r="4" stroke={A} /><circle cx="29" cy="48" r="4" />
    <g stroke={A}><path d="M52 34 a10 10 0 0 1 0 12" /><path d="M60 28 a18 18 0 0 1 0 24" /></g><path d="M78 30 h28 v22 h-28 z M84 30 v-6 a8 8 0 0 1 16 0 v6" stroke={B} /></g>),
  push_button_start: (<g><circle cx="60" cy="38" r="26" /><circle cx="60" cy="38" r="18" stroke={A} /><path d="M60 26 v10" stroke={A} strokeWidth="3" />
    <path d="M52 30 a11 11 0 1 0 16 0" stroke={A} strokeWidth="3" /></g>),
  remote_start: (<g><rect x="12" y="14" width="22" height="40" rx="5" stroke={B} /><g stroke={A}><path d="M40 30 a10 10 0 0 1 10 0" /><path d="M38 24 a16 16 0 0 1 14 0" /></g>
    <g transform="translate(40 8) scale(.68)"><CarSide /></g></g>),

  // ── comfort ───────────────────────────────────────────────────────────────────────────
  auto_climate: (<g><rect x="20" y="16" width="80" height="40" rx="8" /><text x="44" y="42" textAnchor="middle" fontSize="15" fontWeight="800" fill={A} stroke="none">22°</text>
    <path d="M72 28 h18 M72 36 h14 M72 44 h18" stroke={B} /></g>),
  rear_ac_vents: (<g><path d="M24 64 L36 14 L84 14 L96 64" opacity=".5" /><rect x="46" y="30" width="28" height="16" rx="4" /><path d="M50 36 h20 M50 40 h20" />
    <g stroke={B}><path d="M60 50 q-6 6 0 12" /><path d="M50 50 q-8 6 -4 12" /><path d="M70 50 q8 6 4 12" /></g></g>),
  ventilated_seats: (<g><path d="M40 10 Q34 40 40 50 L90 50 Q94 58 86 62 L40 62 Q28 58 30 40 Q30 18 40 10 Z" />
    <g fill={B} stroke="none">{[22, 32, 42].map((y) => [44, 52, 60].map((x) => <circle key={`${x}${y}`} cx={x - (y - 22) / 6} cy={y} r="1.8" />))}</g>
    <g stroke={B}><path d="M98 18 q-6 6 0 12 q6 6 0 12" /><path d="M108 18 q-6 6 0 12 q6 6 0 12" opacity=".6" /></g></g>),
  powered_driver_seat: (<g><path d="M40 10 Q34 40 40 50 L90 50 Q94 58 86 62 L40 62 Q28 58 30 40 Q30 18 40 10 Z" />
    <g stroke={A}><path d="M98 24 v20 M94 28 l4 -4 l4 4 M94 40 l4 4 l4 -4" /><path d="M54 68 h28 M58 64 l-4 4 l4 4 M78 64 l4 4 l-4 4" /></g></g>),
  sunroof: (<g><CarSide /><path d="M54 24 L74 24" stroke={A} strokeWidth="3.5" /><path d="M76 20 L86 20" stroke={B} strokeWidth="2" /><path d="M66 6 l0 10 M60 10 l6 6 l6 -6" stroke={B} /></g>),
  panoramic_sunroof: (<g><CarTop /><rect x="44" y="20" width="32" height="30" rx="5" fill={A} fillOpacity=".18" stroke={A} /></g>),
  ambient_lighting: (<g><path d="M6 56 Q60 30 114 56" /><path d="M14 50 Q60 28 106 50" stroke={A} strokeWidth="2.5" opacity=".9" />
    <path d="M20 62 Q60 46 100 62" stroke={B} strokeWidth="2" opacity=".8" /></g>),
  cooled_glovebox: (<g><rect x="22" y="22" width="76" height="34" rx="6" /><path d="M22 34 h76" /><circle cx="60" cy="28" r="2" />
    <g stroke={B}><path d="M48 46 l6 -6 l6 6 l6 -6 l6 6" /></g></g>),
  rear_armrest: (<g><path d="M14 20 L18 60 L102 60 L106 20" opacity=".5" /><rect x="50" y="34" width="20" height="14" rx="4" stroke={A} /><circle cx="56" cy="41" r="2.5" stroke={A} /><circle cx="64" cy="41" r="2.5" stroke={A} /></g>),
  height_adjustable_seat: (<g><path d="M40 10 Q34 40 40 50 L90 50 Q94 58 86 62 L40 62 Q28 58 30 40 Q30 18 40 10 Z" />
    <path d="M104 22 v34 M98 28 l6 -6 l6 6 M98 50 l6 6 l6 -6" stroke={A} /></g>),

  // ── styling ───────────────────────────────────────────────────────────────────────────
  led_headlamps: (<g><path d="M10 26 Q30 14 64 20 L64 52 Q30 58 10 46 Z" /><g fill={A} stroke="none">{[22, 32, 42, 52].map((x) => <rect key={x} x={x} y="30" width="5" height="12" rx="1.5" />)}</g>
    <path d="M70 28 L112 18 M70 36 L114 36 M70 44 L112 54" stroke={B} /></g>),
  led_drl: (<g><path d="M10 26 Q30 14 64 20 L64 52 Q30 58 10 46 Z" /><path d="M16 28 Q34 20 58 24" stroke={A} strokeWidth="3.5" /></g>),
  alloy_wheels: (<g><circle cx="60" cy="38" r="30" /><circle cx="60" cy="38" r="22" stroke={A} /><circle cx="60" cy="38" r="5" />
    {[0, 72, 144, 216, 288].map((d) => (<path key={d} d={`M60 38 L${60 + 21 * Math.cos((d * Math.PI) / 180)} ${38 + 21 * Math.sin((d * Math.PI) / 180)}`} stroke={A} strokeWidth="3" />))}</g>),
  fog_lamps: (<g><path d="M14 30 L106 30 L100 56 L20 56 Z" /><circle cx="30" cy="48" r="5" stroke={A} /><circle cx="90" cy="48" r="5" stroke={A} />
    <path d="M24 60 L10 68 M36 60 L36 70 M84 60 L84 70 M96 60 L110 68" stroke={B} strokeDasharray="2 3" /></g>),
  roof_rails: (<g><CarSide /><path d="M44 21 L90 21" stroke={A} strokeWidth="3" /><path d="M48 21 v4 M86 21 v4" stroke={A} /></g>),

  // ── two-wheelers ─────────────────────────────────────────────────────────────────────
  abs_dual: (<g><circle cx="26" cy="48" r="16" /><circle cx="94" cy="48" r="16" /><path d="M26 48 L50 26 L80 26 L94 48 M50 26 L60 48 L80 26" opacity=".6" />
    <text x="26" y="52" textAnchor="middle" fontSize="9" fontWeight="800" fill={A} stroke="none">ABS</text><text x="94" y="52" textAnchor="middle" fontSize="9" fontWeight="800" fill={A} stroke="none">ABS</text></g>),
  abs_single: (<g><circle cx="26" cy="48" r="16" /><circle cx="94" cy="48" r="16" /><path d="M26 48 L50 26 L80 26 L94 48 M50 26 L60 48 L80 26" opacity=".6" />
    <text x="94" y="52" textAnchor="middle" fontSize="9" fontWeight="800" fill={A} stroke="none">ABS</text></g>),
  cbs: (<g><circle cx="26" cy="48" r="16" /><circle cx="94" cy="48" r="16" /><path d="M26 48 Q60 10 94 48" stroke={A} strokeDasharray="4 3" /><path d="M58 30 h8" stroke={A} strokeWidth="3" /></g>),
  tft_display: (<g><rect x="18" y="14" width="84" height="46" rx="10" /><circle cx="44" cy="37" r="14" stroke={A} /><path d="M44 37 L52 29" stroke={A} />
    <path d="M70 26 h22 M70 34 h16 M70 42 h22" stroke={B} /></g>),
  bluetooth_console: (<g><rect x="18" y="14" width="56" height="46" rx="10" /><path d="M88 22 l12 10 l-12 10 l0 -24 l12 10 l-12 10 0 0" stroke={B} /><path d="M30 30 h32 M30 40 h22" stroke={A} /></g>),
  usb_charging: (<g><rect x="30" y="26" width="40" height="22" rx="4" /><rect x="40" y="33" width="20" height="8" rx="1.5" stroke={A} /><path d="M70 37 h24 l8 -8" stroke={B} /><path d="M86 18 l-5 9 h7 l-5 9" stroke={A} /></g>),
  traction_control: (<g><circle cx="60" cy="40" r="24" /><path d="M36 64 Q60 52 84 64" stroke={B} /><path d="M50 30 q10 -10 20 0 M48 46 q12 10 24 0" stroke={A} /></g>),
  ride_modes: (<g><rect x="20" y="18" width="80" height="38" rx="8" /><g fontSize="9" fontWeight="800" stroke="none"><text x="36" y="41" textAnchor="middle" fill="currentColor">ECO</text>
    <text x="60" y="41" textAnchor="middle" fill={A}>RAIN</text><text x="86" y="41" textAnchor="middle" fill="currentColor">SPORT</text></g></g>),
  slipper_clutch: (<g><circle cx="60" cy="38" r="26" /><circle cx="60" cy="38" r="14" stroke={A} />{[0, 45, 90, 135, 180, 225, 270, 315].map((d) => (
    <path key={d} d={`M${60 + 14 * Math.cos((d * Math.PI) / 180)} ${38 + 14 * Math.sin((d * Math.PI) / 180)} L${60 + 26 * Math.cos(((d + 12) * Math.PI) / 180)} ${38 + 26 * Math.sin(((d + 12) * Math.PI) / 180)}`} stroke={B} />))}</g>),
  led_lamps_2w: (<g><circle cx="44" cy="38" r="20" /><g fill={A} stroke="none">{[30, 38, 46, 54].map((x) => <rect key={x} x={x - 2} y="34" width="4" height="8" rx="1" />)}</g>
    <path d="M68 28 L112 18 M68 38 L114 38 M68 48 L112 58" stroke={B} /></g>),
};

export const ART_KEYS = Object.keys(ART);

export function EquipmentArt({ k, className }: { k: string; className?: string }) {
  const art = ART[k];
  if (!art) return null;
  return (
    <svg viewBox="0 0 120 72" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {art}
    </svg>
  );
}
