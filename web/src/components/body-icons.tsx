import React from "react";

// Precision automotive silhouettes for vehicle body types, with accurate proportions,
// distinct greenhouse/pillars, ground clearance and wheel positioning.

type IconProps = { className?: string };

function SedanIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Aerodynamic 3-box Sedan with distinct bonnet, windshield, roof, rear screen, and horizontal boot */}
      <path d="M4 28 C4 24, 6 23, 9 23 L18 21 C20 21, 22 19, 24 15 L29 10 C31 8, 33 8, 36 8 L46 8 C49 8, 51 9, 53 13 L57 20 L64 21 C67 21, 68 23, 68 26 L67 29 L59 29" />
      <path d="M23 29 L45 29 M4 29 L11 29" />
      {/* Sedan Greenhouse with dual side windows & B-pillar */}
      <path d="M26 20 L30 11 L46 11 L52 20 Z" />
      <line x1="39" y1="11" x2="39" y2="20" strokeWidth="1.8" />
      {/* Sports Sedan Wheels */}
      <circle cx="17" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="52" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="17" cy="29" r="2" fill="currentColor" />
      <circle cx="52" cy="29" r="2" fill="currentColor" />
    </svg>
  );
}

function SuvIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Roof rails */}
      <path d="M26 4 L54 4" strokeWidth="1.8" />
      <line x1="30" y1="4" x2="30" y2="7" strokeWidth="1.5" />
      <line x1="50" y1="4" x2="50" y2="7" strokeWidth="1.5" />
      {/* Rugged upright 2-box SUV with high stance & vertical rear tailgate */}
      <path d="M4 27 L4 18 C4 17, 6 16, 8 16 L20 15 C22 15, 23 13, 24 10 L26 7 C27 6, 28 6, 30 6 L56 6 C58 6, 59 7, 60 9 L63 17 L64 24 C64 26, 63 27, 60 27 L57 27" />
      {/* High ground clearance underbody */}
      <path d="M23 27 L44 27 M4 27 L11 27" />
      {/* 3-window SUV cabin glasshouse */}
      <path d="M27 14 L28 9 L56 9 L59 14 Z" />
      <line x1="38" y1="9" x2="38" y2="14" strokeWidth="1.8" />
      <line x1="49" y1="9" x2="49" y2="14" strokeWidth="1.8" />
      {/* Large SUV Wheels */}
      <circle cx="17" cy="27" r="5.5" strokeWidth="2" />
      <circle cx="50" cy="27" r="5.5" strokeWidth="2" />
      <circle cx="17" cy="27" r="2" fill="currentColor" />
      <circle cx="50" cy="27" r="2" fill="currentColor" />
    </svg>
  );
}

function HatchbackIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Compact 2-box with steep rear hatch and short overhangs */}
      <path d="M4 28 C4 24, 6 23, 9 23 L18 21 C20 21, 22 19, 24 15 L28 10 C30 8, 32 8, 35 8 L44 8 C47 8, 49 9, 51 12 L56 20 L57 26 C57 28, 56 29, 54 29 L54 29" />
      <path d="M23 29 L43 29 M4 29 L11 29" />
      {/* Sporty Hatchback Windows */}
      <path d="M26 20 L30 11 L44 11 L49 20 Z" />
      <line x1="38" y1="11" x2="38" y2="20" strokeWidth="1.8" />
      <circle cx="17" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="48" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="17" cy="29" r="2" fill="currentColor" />
      <circle cx="48" cy="29" r="2" fill="currentColor" />
    </svg>
  );
}

function MuvIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Extended 3-row people mover with high continuous roofline */}
      <path d="M4 27 L4 21 C4 19, 6 18, 9 17 L17 15 C19 14, 21 11, 23 8 C24 7, 26 6, 28 6 L59 6 C61 6, 62 7, 63 9 L65 20 L65 25 C65 27, 64 27, 61 27 L58 27" />
      <path d="M22 27 L45 27 M4 27 L10 27" />
      {/* 3-Row Extended Glasshouse */}
      <path d="M25 14 L28 9 L60 9 L62 14 Z" />
      <line x1="38" y1="9" x2="38" y2="14" strokeWidth="1.8" />
      <line x1="50" y1="9" x2="50" y2="14" strokeWidth="1.8" />
      <circle cx="16" cy="27" r="5.5" strokeWidth="2" />
      <circle cx="52" cy="27" r="5.5" strokeWidth="2" />
      <circle cx="16" cy="27" r="2" fill="currentColor" />
      <circle cx="52" cy="27" r="2" fill="currentColor" />
    </svg>
  );
}

function CoupeIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Low-slung performance coupe with sweeping fastback roofline & spoiler */}
      <path d="M4 29 C4 26, 6 25, 9 24 L22 21 C24 21, 27 19, 29 15 L33 11 C35 9, 37 9, 40 9 L45 9 C50 9, 56 12, 60 17 L65 22 C67 24, 67 26, 67 28 L66 29 L58 29" />
      <path d="M24 29 L46 29 M4 29 L12 29" />
      {/* Sleek raked cockpit */}
      <path d="M30 20 L34 12 L44 12 L53 20 Z" />
      <line x1="42" y1="12" x2="42" y2="20" strokeWidth="1.8" />
      <circle cx="18" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="52" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="18" cy="29" r="2" fill="currentColor" />
      <circle cx="52" cy="29" r="2" fill="currentColor" />
    </svg>
  );
}

function PickupIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Dual-cab pickup truck with open rear cargo bed */}
      <path d="M4 27 L4 18 C4 17, 6 16, 8 16 L20 15 C22 15, 23 13, 24 10 L26 7 C27 6, 28 6, 30 6 L43 6 C45 6, 46 7, 47 9 L47 17 L63 17 L64 24 C64 26, 63 27, 60 27 L58 27" />
      <path d="M23 27 L47 27 M4 27 L11 27" />
      {/* Crew Cab windows */}
      <path d="M27 14 L28 9 L44 9 L44 14 Z" />
      <line x1="36" y1="9" x2="36" y2="14" strokeWidth="1.8" />
      <circle cx="17" cy="27" r="5.5" strokeWidth="2" />
      <circle cx="53" cy="27" r="5.5" strokeWidth="2" />
      <circle cx="17" cy="27" r="2" fill="currentColor" />
      <circle cx="53" cy="27" r="2" fill="currentColor" />
    </svg>
  );
}

function ConvertibleIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Open-top roadster with raked windscreen and exposed sport headrest */}
      <path d="M4 29 C4 26, 6 25, 9 24 L22 21 C24 21, 26 18, 28 14 L30 11 C31 9, 32 9, 34 10 L33 21 L43 21 C45 17, 48 17, 49 21 L62 22 C66 22, 67 24, 67 27 L66 29 L58 29" />
      <path d="M24 29 L46 29 M4 29 L12 29" />
      {/* Windshield frame & headrest hoop */}
      <path d="M28 20 L31 11" strokeWidth="2.2" />
      <path d="M44 20 C44 16, 48 16, 48 20" strokeWidth="1.8" />
      <circle cx="18" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="52" cy="29" r="5.2" strokeWidth="2" />
      <circle cx="18" cy="29" r="2" fill="currentColor" />
      <circle cx="52" cy="29" r="2" fill="currentColor" />
    </svg>
  );
}

function CruiserIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Raked front fork and high cruiser handlebars */}
      <path d="M53 29 L48 14 L44 9" strokeWidth="2.2" />
      <path d="M42 9 L46 9" strokeWidth="2.5" />
      {/* Tear-drop fuel tank & low scooped saddle */}
      <path d="M46 16 C42 14, 36 14, 33 17 C30 19, 27 21, 24 21 L20 22 C17 22, 16 25, 17 28" />
      {/* Engine block & exhaust pipe */}
      <path d="M33 21 L32 28 L44 28" />
      <path d="M33 26 L20 27" strokeWidth="2.2" />
      {/* Spoked cruiser wheels */}
      <circle cx="18" cy="28" r="6" strokeWidth="2" />
      <circle cx="53" cy="28" r="6" strokeWidth="2" />
      <circle cx="18" cy="28" r="2" fill="currentColor" />
      <circle cx="53" cy="28" r="2" fill="currentColor" />
    </svg>
  );
}

function ScooterIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Front apron, handlebar cowl & step-through floorboard */}
      <path d="M51 29 L49 19 L46 11 L43 11" strokeWidth="2.2" />
      <path d="M41 11 L47 11" strokeWidth="2.5" />
      <path d="M48 20 L38 27 L28 27 L25 19 C25 18, 30 18, 35 18 L24 22 C21 22, 19 25, 19 28" />
      {/* Compact 10/12-inch scooter wheels */}
      <circle cx="21" cy="29" r="4.8" strokeWidth="2" />
      <circle cx="50" cy="29" r="4.8" strokeWidth="2" />
      <circle cx="21" cy="29" r="1.8" fill="currentColor" />
      <circle cx="50" cy="29" r="1.8" fill="currentColor" />
    </svg>
  );
}

function SportsBikeIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Aggressive aerodynamic fairing & clip-on handlebars */}
      <path d="M51 28 L45 15 L48 11 L43 11" strokeWidth="2.2" />
      {/* Sculpted muscular tank, split step-up seat & sharp tail cowl */}
      <path d="M46 15 C42 12, 36 12, 34 16 L29 19 L23 15 L17 14 L20 23" />
      {/* Delta box frame & upswept exhaust */}
      <path d="M34 18 L32 27 L43 27" />
      <path d="M30 25 L21 21" strokeWidth="2" />
      {/* 17-inch alloy wheels */}
      <circle cx="19" cy="28" r="5.5" strokeWidth="2" />
      <circle cx="51" cy="28" r="5.5" strokeWidth="2" />
      <circle cx="19" cy="28" r="2" fill="currentColor" />
      <circle cx="51" cy="28" r="2" fill="currentColor" />
    </svg>
  );
}

function AdventureBikeIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Tall windscreen, rally beak & long-travel USD suspension */}
      <path d="M53 28 L46 12 L44 7 M46 14 L52 14" strokeWidth="2.2" />
      {/* Upright tank, wide touring seat & high ground clearance */}
      <path d="M44 14 C40 13, 35 14, 33 18 L26 19 L20 18 L19 25" />
      <path d="M33 20 L30 27 L41 27" />
      {/* 21-inch front spoke wheel and 17-inch rear wheel */}
      <circle cx="19" cy="28" r="5.5" strokeWidth="2" />
      <circle cx="53" cy="27" r="6.5" strokeWidth="2" />
      <circle cx="19" cy="28" r="2" fill="currentColor" />
      <circle cx="53" cy="27" r="2" fill="currentColor" />
    </svg>
  );
}

function CommuterBikeIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 72 40" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* Classic upright commuter stance with bikini fairing */}
      <path d="M51 28 L46 15 L44 10 M42 10 L46 10" strokeWidth="2.2" />
      {/* Practical flat single seat and commuter tank */}
      <path d="M44 15 C40 14, 35 14, 33 17 L22 17 C19 17, 18 20, 18 25" />
      <path d="M33 19 L31 27 L42 27" />
      <circle cx="19" cy="28" r="5.5" strokeWidth="2" />
      <circle cx="51" cy="28" r="5.5" strokeWidth="2" />
      <circle cx="19" cy="28" r="2" fill="currentColor" />
      <circle cx="51" cy="28" r="2" fill="currentColor" />
    </svg>
  );
}

const REGISTRY: Record<string, React.ComponentType<IconProps>> = {
  sedan: SedanIcon,
  suv: SuvIcon,
  hatchback: HatchbackIcon,
  muv: MuvIcon,
  mpv: MuvIcon,
  coupe: CoupeIcon,
  pickup: PickupIcon,
  convertible: ConvertibleIcon,
  cruiser: CruiserIcon,
  scooter: ScooterIcon,
  sports: SportsBikeIcon,
  sportbike: SportsBikeIcon,
  naked: SportsBikeIcon,
  adventure: AdventureBikeIcon,
  commuter: CommuterBikeIcon,
  bike: CommuterBikeIcon,
  motorcycle: CruiserIcon,
  street: SportsBikeIcon,
  "modern classic": CruiserIcon,
  roadster: SportsBikeIcon,
  electric: ScooterIcon,
  "electric scooter": ScooterIcon,
  tourer: AdventureBikeIcon,
  superbike: SportsBikeIcon,
  sportss: SportsBikeIcon,
};

export function BodyIcon({ type, className }: { type: string; className?: string }) {
  const norm = (type || "").trim().toLowerCase();
  const Component = REGISTRY[norm] ?? SuvIcon;
  return <Component className={className} />;
}

export const BODY_TYPES = ["Hatchback", "Sedan", "SUV", "MUV", "Pickup", "Coupe", "Convertible"];
export const BIKE_BODY_TYPES = ["Commuter", "Scooter", "Cruiser", "Sports", "Adventure"];
