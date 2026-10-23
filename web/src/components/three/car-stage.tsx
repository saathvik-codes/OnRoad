"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { ContactShadows, Environment, Lightformer, MeshReflectorMaterial, OrbitControls } from "@react-three/drei";
import { Suspense, useRef, useState } from "react";
import type { MotionValue } from "motion/react";
import * as THREE from "three";
import { HeroCar } from "./hero-car";

export type StageShot = { angle: number; height: number; distance: number; explode: number };

// Scroll chapters: each key frame is a camera angle around the car, height, distance and how far it is exploded
export const DEFAULT_SHOTS: StageShot[] = [
  { angle: -0.6, height: 1.4, distance: 8.2, explode: 0 },     // reveal, three-quarter front
  { angle: 0.9, height: 1.1, distance: 6.6, explode: 0 },      // side profile
  { angle: 2.2, height: 3.4, distance: 9.4, explode: 1 },      // exploded from above: body lifts, wheels slide out
  { angle: 3.6, height: 0.9, distance: 6.2, explode: 0.35 },   // rear three-quarter, low
  { angle: 5.4, height: 1.6, distance: 7.6, explode: 0 },      // back to a hero shot
];

function interp(shots: StageShot[], p: number): StageShot {
  const t = Math.min(Math.max(p, 0), 1) * (shots.length - 1);
  const i = Math.min(Math.floor(t), shots.length - 2);
  const f = THREE.MathUtils.smoothstep(t - i, 0, 1);
  const a = shots[i], b = shots[i + 1];
  return { angle: a.angle + (b.angle - a.angle) * f, height: a.height + (b.height - a.height) * f,
           distance: a.distance + (b.distance - a.distance) * f, explode: a.explode + (b.explode - a.explode) * f };
}

function Director({ progress, shots, spin, setExplode, lookOffset }: { progress?: MotionValue<number>; shots: StageShot[]; spin: boolean; setExplode: (v: number) => void; lookOffset: number }) {
  const last = useRef(-1);
  useFrame((state) => {
    const s = interp(shots, progress?.get() ?? 0);
    const angle = s.angle + (spin ? state.clock.elapsedTime * 0.08 : 0);
    const want = new THREE.Vector3(Math.sin(angle) * s.distance, s.height, Math.cos(angle) * s.distance);
    state.camera.position.lerp(want, 0.06);
    // on wide screens aim left of the car so it sits on the right, clear of the headline
    const off = state.size.width > 900 ? lookOffset : 0;
    state.camera.lookAt(-off * Math.cos(angle), 0.55, off * Math.sin(angle));
    const e = Math.round(s.explode * 100) / 100;
    if (e !== last.current) { last.current = e; setExplode(e); }
  });
  return null;
}

export function CarStage({ paint = "#b3121f", progress, shots = DEFAULT_SHOTS, interactive = false, spin = false, lookOffset = 0, className }:
  { paint?: string; progress?: MotionValue<number>; shots?: StageShot[]; interactive?: boolean; spin?: boolean; lookOffset?: number; className?: string }) {
  const [explode, setExplode] = useState(0);
  return (
    <div className={className}>
      <Canvas shadows dpr={[1, 1.75]} camera={{ position: [5, 1.4, 6.5], fov: 30 }}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.05 }}>
        <color attach="background" args={["#05060a"]} />
        <fog attach="fog" args={["#05060a", 10, 26]} />
        <Suspense fallback={null}>
          <HeroCar paint={paint} explode={explode} />
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[60, 60]} />
            <MeshReflectorMaterial blur={[300, 90]} resolution={1024} mixBlur={1} mixStrength={12} roughness={0.9}
              depthScale={1} minDepthThreshold={0.4} maxDepthThreshold={1.2} color="#08090d" metalness={0.5} mirror={0.5} />
          </mesh>
          <ContactShadows position={[0, 0.004, 0]} opacity={0.8} scale={14} blur={2.2} far={3} />
          {/* studio light panels: no external HDR download */}
          <Environment resolution={512} frames={1} environmentIntensity={1.35}>
            <Lightformer intensity={2.6} position={[0, 7, 0]} rotation-x={Math.PI / 2} scale={[14, 4, 1]} />
            <Lightformer intensity={2} position={[-7, 2.5, 1]} rotation-y={Math.PI / 2} scale={[10, 2.4, 1]} color="#a8d4ff" />
            <Lightformer intensity={2} position={[7, 2.5, -1]} rotation-y={-Math.PI / 2} scale={[10, 2.4, 1]} color="#ffd6a8" />
            <Lightformer form="ring" intensity={5} position={[3, 4, 7]} scale={3} />
            <Lightformer intensity={1.2} position={[0, 1, -8]} scale={[16, 1.5, 1]} color="#ff6a3d" />
          </Environment>
          <spotLight position={[5, 9, 5]} angle={0.45} penumbra={1} intensity={80} castShadow shadow-mapSize={[2048, 2048]} />
        </Suspense>
        {interactive ? (
          <OrbitControls enablePan={false} minDistance={5} maxDistance={11} minPolarAngle={0.6} maxPolarAngle={1.5} target={[0, 0.55, 0]} autoRotate autoRotateSpeed={0.6} />
        ) : (
          <Director progress={progress} shots={shots} spin={spin} setExplode={setExplode} lookOffset={lookOffset} />
        )}
      </Canvas>
    </div>
  );
}
