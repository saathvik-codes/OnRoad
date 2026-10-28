"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  VolumeX, 
  Maximize2, 
  Gauge, 
  Sparkles, 
  Compass, 
  Layers, 
  SlidersHorizontal,
  ChevronRight,
  ShieldAlert,
  Zap,
  Radio
} from "lucide-react";
import { cn } from "@/components/ui";

interface Chapter {
  id: number;
  time: number; // in seconds
  title: string;
  subtitle: string;
  telemetry: {
    stat1: { label: string; value: string };
    stat2: { label: string; value: string };
    stat3: { label: string; value: string };
  };
  image: string;
  description: string;
}

const CHAPTERS: Chapter[] = [
  {
    id: 1,
    time: 0,
    title: "Horizon LED Lightbar & Front Fascia",
    subtitle: "Aerodynamic sculpted nose with seamless full-width DRL signature",
    telemetry: {
      stat1: { label: "Drag Coeff", value: "0.31 Cd" },
      stat2: { label: "Lighting", value: "Full LED Projector" },
      stat3: { label: "Width", value: "1,775 mm" },
    },
    image: "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
    description: "The refreshed Hyundai Bayon debuts an edge-to-edge seamless horizon LED bar across the clamshell bonnet line, paired with arrow-head lower bumper inserts and a rugged silver skid plate.",
  },
  {
    id: 2,
    time: 48,
    title: "1.0L T-GDi Mild-Hybrid Powertrain",
    subtitle: "48-Volt electrified booster with 7-speed dual-clutch transmission",
    telemetry: {
      stat1: { label: "Peak Power", value: "120 PS @ 6000 rpm" },
      stat2: { label: "Max Torque", value: "172 Nm @ 1500-4000 rpm" },
      stat3: { label: "0-100 km/h", value: "10.4 sec" },
    },
    image: "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=1200&q=80",
    description: "Under the hood sits Hyundai's tuned 1.0-litre 3-cylinder turbocharged gasoline direct injection engine integrated with a 48V starter-generator that recovers braking kinetic energy and assists off-the-line acceleration.",
  },
  {
    id: 3,
    time: 95,
    title: "Dual 10.25-inch Panoramic Digital Cockpit",
    subtitle: "Customizable driver instrumentation, OTA updates & Bose audio",
    telemetry: {
      stat1: { label: "Twin Displays", value: "10.25\" + 10.25\"" },
      stat2: { label: "Sound System", value: "8-Spk Bose Premium" },
      stat3: { label: "Cabin Ambience", value: "64 Colors Multi-LED" },
    },
    image: "https://images.unsplash.com/photo-1508974239320-0a029497e820?auto=format&fit=crop&w=1200&q=80",
    description: "Inside, the Bayon features horizontal blade dash vanes integrating air vents, twin floating high-res screens with wireless smartphone pairing, Bluelink connected car tech, and wireless phone charging pad.",
  },
  {
    id: 4,
    time: 142,
    title: "Hyundai SmartSense L2 ADAS Radar Suite",
    subtitle: "Autonomous emergency braking, lane following & blind spot monitoring",
    telemetry: {
      stat1: { label: "Airbags", value: "6 Standard" },
      stat2: { label: "Radar/Cam", value: "Front & Rear Cross" },
      stat3: { label: "Safety Rating", value: "5-Star Euro NCAP standard" },
    },
    image: "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80",
    description: "Equipped with front monocular camera and millimeter-wave radar for Forward Collision-Avoidance with pedestrian & cyclist detection, Lane Keeping Assist, High Beam Assist, and Smart Cruise Control.",
  },
  {
    id: 5,
    time: 195,
    title: "India Expected Launch & On-Road Economics",
    subtitle: "Sub-4m crossover slotting alongside Venue with ₹8.49L - ₹12.80L ex-showroom",
    telemetry: {
      stat1: { label: "Est. Base Price", value: "₹8.49 Lakh" },
      stat2: { label: "Top N-Line DCT", value: "₹12.80 Lakh" },
      stat3: { label: "Boot Volume", value: "411 Litres" },
    },
    image: "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
    description: "Scheduled for evaluated Indian market introduction in late 2025 to take on the Maruti Fronx, Toyota Taisor, and Skoda Kylaq with premium Euro-spec crossover road dynamics and distinct N Line aero flair.",
  },
];

const TOTAL_DURATION = 230; // 3 min 50 sec

export function NewsVideoPlayer() {
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
  const [showHUD, setShowHUD] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState<1 | 1.25 | 1.5>(1);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const playerContainerRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Playback timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (playing) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          const next = prev + 1 * playbackSpeed;
          if (next >= TOTAL_DURATION) {
            setPlaying(false);
            return 0;
          }
          return next;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [playing, playbackSpeed]);

  // Sync current chapter with currentTime
  useEffect(() => {
    let activeIdx = 0;
    for (let i = 0; i < CHAPTERS.length; i++) {
      if (currentTime >= CHAPTERS[i].time) {
        activeIdx = i;
      }
    }
    setCurrentChapterIndex(activeIdx);
  }, [currentTime]);

  // Ambient sound synthesizer using Web Audio API for subtle cabin audio / engine sound simulation
  const toggleSound = () => {
    if (!soundEnabled) {
      try {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (!audioContextRef.current) {
          audioContextRef.current = new AudioCtx();
        }
        if (audioContextRef.current.state === "suspended") {
          audioContextRef.current.resume();
        }
        // Create subtle engine rumble simulation
        const osc = audioContextRef.current.createOscillator();
        const gain = audioContextRef.current.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(55, audioContextRef.current.currentTime); // low 55Hz idle hum
        gain.gain.setValueAtTime(0.04, audioContextRef.current.currentTime);
        osc.connect(gain);
        gain.connect(audioContextRef.current.destination);
        osc.start();
        setTimeout(() => {
          gain.gain.exponentialRampToValueAtTime(0.0001, (audioContextRef.current?.currentTime || 0) + 2);
          setTimeout(() => osc.stop(), 2100);
        }, 1200);
      } catch (e) {
        console.log("Audio not allowed yet:", e);
      }
      setSoundEnabled(true);
    } else {
      setSoundEnabled(false);
    }
  };

  const jumpToChapter = (idx: number) => {
    setCurrentTime(CHAPTERS[idx].time);
    setCurrentChapterIndex(idx);
    setPlaying(true);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const activeChapter = CHAPTERS[currentChapterIndex];

  return (
    <div 
      ref={playerContainerRef}
      className={cn(
        "relative w-full rounded-2xl overflow-hidden border border-white/10 bg-[#07090e] shadow-2xl transition-all duration-300",
        isFullscreen ? "fixed inset-0 z-50 rounded-none border-none" : "my-8"
      )}
    >
      {/* Top Header Bar / Brand Watermark */}
      <div className="absolute top-0 inset-x-0 z-20 flex items-center justify-between px-5 py-3.5 bg-gradient-to-b from-black/90 via-black/50 to-transparent">
        <div className="flex items-center gap-2.5">
          <span className="flex h-2 w-2 rounded-full bg-accent animate-pulse" />
          <span className="text-xs font-mono font-semibold tracking-wider text-white uppercase">
            OnRoad Motion Theater &bull; Hyundai Bayon Reveal
          </span>
          <span className="hidden sm:inline-block text-[11px] font-mono px-2 py-0.5 rounded-full bg-white/10 text-white/80 border border-white/10">
            4K Interactive Reel
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Telemetry HUD Toggle */}
          <button
            type="button"
            onClick={() => setShowHUD(!showHUD)}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors",
              showHUD 
                ? "bg-accent/20 border-accent/40 text-accent" 
                : "bg-black/60 border-white/10 text-mute hover:text-white"
            )}
          >
            <Gauge className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{showHUD ? "HUD Active" : "Show HUD"}</span>
          </button>

          {/* Sound / Ambient Sim */}
          <button
            type="button"
            onClick={toggleSound}
            className="p-1.5 rounded-lg bg-black/60 border border-white/10 text-mute hover:text-white transition-colors"
            title={soundEnabled ? "Mute Ambient Sound" : "Enable Sound"}
          >
            {soundEnabled ? <Volume2 className="h-4 w-4 text-accent" /> : <VolumeX className="h-4 w-4" />}
          </button>

          {/* Fullscreen */}
          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 rounded-lg bg-black/60 border border-white/10 text-mute hover:text-white transition-colors"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Interactive Stage / Visual Canvas */}
      <div className="relative aspect-video w-full overflow-hidden select-none">
        {/* Background Visual Reel with smooth crossfade */}
        <div 
          className="absolute inset-0 bg-cover bg-center transition-all duration-700 transform scale-105"
          style={{ backgroundImage: `url(${activeChapter.image})` }}
        />
        {/* Cinematic Vignette Overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/30 to-black/60 pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(0,0,0,0.7)_100%)] pointer-events-none" />

        {/* Center Play Button Overlay when paused */}
        {!playing && (
          <div className="absolute inset-0 z-10 flex items-center justify-center">
            <button
              type="button"
              onClick={() => setPlaying(true)}
              className="group flex h-20 w-20 items-center justify-center rounded-full bg-accent/90 text-white shadow-2xl backdrop-blur-md transition-all duration-300 hover:scale-110 hover:bg-accent active:scale-95 border-2 border-white/30"
              aria-label="Play Reveal Reel"
            >
              <Play className="h-8 w-8 ml-1 fill-white transition-transform group-hover:scale-105" />
            </button>
          </div>
        )}

        {/* Live Synced Telemetry HUD Overlay */}
        {showHUD && (
          <div className="absolute top-16 right-5 z-10 w-72 max-w-[85vw] rounded-xl border border-white/15 bg-black/75 p-3.5 backdrop-blur-md shadow-xl text-left pointer-events-none transition-all duration-300">
            <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2.5">
              <div className="flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-accent" />
                <span className="text-[11px] font-mono uppercase tracking-wider text-white font-bold">
                  Telemetry Spec HUD
                </span>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                LIVE SYNC
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-lg bg-white/5 p-2 border border-white/5">
                <p className="text-[10px] text-mute font-mono">{activeChapter.telemetry.stat1.label}</p>
                <p className="text-xs font-bold text-white font-mono mt-0.5">{activeChapter.telemetry.stat1.value}</p>
              </div>
              <div className="rounded-lg bg-white/5 p-2 border border-white/5">
                <p className="text-[10px] text-mute font-mono">{activeChapter.telemetry.stat2.label}</p>
                <p className="text-xs font-bold text-white font-mono mt-0.5">{activeChapter.telemetry.stat2.value}</p>
              </div>
              <div className="rounded-lg bg-white/5 p-2 border border-white/5">
                <p className="text-[10px] text-mute font-mono">{activeChapter.telemetry.stat3.label}</p>
                <p className="text-xs font-bold text-white font-mono mt-0.5">{activeChapter.telemetry.stat3.value}</p>
              </div>
            </div>

            <p className="mt-2 text-[11px] text-white/80 leading-relaxed line-clamp-2">
              {activeChapter.description}
            </p>
          </div>
        )}

        {/* Chapter Title Badge Overlay at bottom-left */}
        <div className="absolute bottom-20 left-5 right-5 sm:right-auto z-10 text-left pointer-events-none">
          <div className="inline-flex items-center gap-2 rounded-full bg-black/60 px-3 py-1 text-xs font-mono text-accent border border-accent/30 backdrop-blur-md mb-2">
            <span>Chapter 0{activeChapter.id} / 05</span>
            <span className="text-white/40">&bull;</span>
            <span className="text-white/80">{formatTime(currentTime)}</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-white font-[family-name:var(--font-display)] drop-shadow-md">
            {activeChapter.title}
          </h3>
          <p className="text-xs sm:text-sm text-white/80 max-w-xl drop-shadow line-clamp-2">
            {activeChapter.subtitle}
          </p>
        </div>
      </div>

      {/* Interactive Controls & Chapter Scrubber Bar */}
      <div className="relative z-20 border-t border-white/10 bg-black/90 p-4 backdrop-blur-md">
        {/* Scrubber Timeline */}
        <div className="relative mb-3 flex items-center">
          <input
            type="range"
            min={0}
            max={TOTAL_DURATION}
            value={currentTime}
            onChange={(e) => {
              setCurrentTime(Number(e.target.value));
            }}
            className="w-full h-1.5 bg-white/15 rounded-lg appearance-none cursor-pointer accent-accent"
          />
        </div>

        {/* Timeline Chapters Marks */}
        <div className="hidden sm:grid grid-cols-5 gap-2 mb-3">
          {CHAPTERS.map((ch, idx) => (
            <button
              key={ch.id}
              type="button"
              onClick={() => jumpToChapter(idx)}
              className={cn(
                "group text-left px-2.5 py-1.5 rounded-lg border transition-all text-xs",
                currentChapterIndex === idx
                  ? "bg-accent/15 border-accent text-white"
                  : "bg-white/[0.03] border-white/5 text-mute hover:border-white/20 hover:text-white"
              )}
            >
              <div className="flex items-center justify-between font-mono text-[10px] text-mute mb-0.5">
                <span>0{ch.id}</span>
                <span>{formatTime(ch.time)}</span>
              </div>
              <p className="font-medium truncate text-[11px] group-hover:text-accent transition-colors">
                {ch.title.split("&")[0].trim()}
              </p>
            </button>
          ))}
        </div>

        {/* Player Controls Bar */}
        <div className="flex items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            {/* Play/Pause Button */}
            <button
              type="button"
              onClick={() => setPlaying(!playing)}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-white shadow-sm hover:brightness-110 active:scale-95 transition"
            >
              {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5 fill-white" />}
            </button>

            {/* Restart */}
            <button
              type="button"
              onClick={() => {
                setCurrentTime(0);
                setCurrentChapterIndex(0);
                setPlaying(true);
              }}
              className="p-2 rounded-lg text-mute hover:text-white hover:bg-white/5 transition"
              title="Restart"
            >
              <RotateCcw className="h-4 w-4" />
            </button>

            {/* Timer readout */}
            <span className="font-mono text-mute text-xs">
              <span className="text-white font-medium">{formatTime(currentTime)}</span> / {formatTime(TOTAL_DURATION)}
            </span>
          </div>

          {/* Right Action Controls: Speed toggle & Chapter Dropdown */}
          <div className="flex items-center gap-2">
            {/* Speed Toggle */}
            <div className="flex items-center rounded-lg border border-white/10 bg-white/5 p-0.5">
              {([1, 1.25, 1.5] as const).map((spd) => (
                <button
                  key={spd}
                  type="button"
                  onClick={() => setPlaybackSpeed(spd)}
                  className={cn(
                    "px-2 py-0.5 rounded text-[11px] font-mono transition-colors",
                    playbackSpeed === spd
                      ? "bg-accent text-white font-bold"
                      : "text-mute hover:text-white"
                  )}
                >
                  {spd}x
                </button>
              ))}
            </div>

            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[11px] text-mute">
              <Radio className="h-3 w-3 text-emerald-400 animate-pulse" />
              <span>Synced 120 FPS Native Motion</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
