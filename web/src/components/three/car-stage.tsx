"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { ContactShadows, Environment, Lightformer, MeshReflectorMaterial, OrbitControls } from "@react-three/drei";
import { Suspense, useMemo, useRef, useState } from "react";
import type { MotionValue } from "motion/react";
import * as THREE from "three";
import { HeroCar, type Anchors, type CarFx } from "./hero-car";
import { EngineFx } from "./engine-fx";

const UP = new THREE.Vector3(0, 1, 0);

/** One scroll key frame: where the camera is, what it looks at, lens, and what the car is doing. */
type Shot = { pos: THREE.Vector3; target: THREE.Vector3; fov: number; explode: number; wheel: number; pedal: number; hood: number;
              engine: number; offset: number };

/** Cinematic path built from the model's own anchor points: reveal → side sweep → through the windscreen →
 *  driver's seat (wheel turns, throttle down) → bonnet opens, dive to the pumping engine → exploded view → low hero finish. */
function buildShots(a: Anchors): { shots: Shot[] } {
  const f = a.forward.clone();
  const r = new THREE.Vector3().crossVectors(f, UP).normalize();
  const S = a.steering.clone(), E = a.engine.clone();
  const toEngine = E.clone().sub(S).setY(0).normalize();          // works for front- or rear-engined layouts
  const mid = new THREE.Vector3(0, 0.6, 0);
  const v = (...parts: [THREE.Vector3, number][]) => parts.reduce((acc, [d, k]) => acc.addScaledVector(d, k), new THREE.Vector3());
  const base = { explode: 0, wheel: 0, pedal: 0, hood: 0, engine: 0, offset: 0 };
  const shots: Shot[] = [
    { ...base, pos: v([f, 5.6], [r, -5.4], [UP, 1.5]), target: mid.clone(), fov: 30, offset: 1 },                         // reveal
    { ...base, pos: v([r, -7.2], [f, -0.8], [UP, 0.7]), target: mid.clone(), fov: 26, offset: 1 },                        // low side sweep
    { ...base, pos: v([S, 1], [f, 2.6], [UP, 0.55]), target: S.clone(), fov: 38 },                                          // at the windscreen
    { ...base, pos: v([S, 1], [f, -0.62], [UP, 0.3]), target: v([S, 1], [f, 1.6], [UP, -0.12]), fov: 64, wheel: -1.4, pedal: 1 }, // driver's seat
    { ...base, pos: v([E, 1], [toEngine, 1.3], [UP, 1.7]), target: E.clone(), fov: 44, hood: 1, engine: 0.6 },              // bonnet up
    { ...base, pos: v([E, 1], [toEngine, 0.9], [r, 1.1], [UP, 1.15]), target: v([E, 1], [UP, 0.1]), fov: 46, hood: 1, engine: 1 }, // inside the engine
    { ...base, pos: v([f, 4.2], [r, 6], [UP, 4.6]), target: v([UP, 0.9]), fov: 34, explode: 1, offset: 1 },               // exploded
    { ...base, pos: v([f, 8.4], [r, 3.4], [UP, 0.45]), target: mid.clone(), fov: 28, offset: 0.55 },                          // low hero finish
  ];
  return { shots };
}

function sample(shots: Shot[], p: number, out: Shot) {
  const t = Math.min(Math.max(p, 0), 1) * (shots.length - 1);
  const i = Math.min(Math.floor(t), shots.length - 2);
  const k = THREE.MathUtils.smootherstep(t - i, 0, 1);
  const a = shots[i], b = shots[i + 1];
  out.pos.lerpVectors(a.pos, b.pos, k);
  out.target.lerpVectors(a.target, b.target, k);
  for (const key of ["fov", "explode", "wheel", "pedal", "hood", "engine", "offset"] as const) out[key] = a[key] + (b[key] - a[key]) * k;
  return out;
}

function Director({ progress, shots, spin, lookOffset, fx, engine }: { progress?: MotionValue<number>; shots: Shot[]; spin: boolean;
  lookOffset: number; fx: React.RefObject<CarFx>; engine: React.RefObject<number> }) {
  const cur = useMemo<Shot>(() => ({ ...shots[0], pos: new THREE.Vector3(), target: new THREE.Vector3() }), [shots]);
  const look = useRef(new THREE.Vector3(0, 0.6, 0));
  const tmp = useMemo(() => ({ right: new THREE.Vector3(), want: new THREE.Vector3() }), []);
  useFrame((state, dt) => {
    const s = sample(shots, progress?.get() ?? 0, cur);
    const k = 1 - Math.exp(-5 * dt);
    const cam = state.camera as THREE.PerspectiveCamera;
    tmp.want.copy(s.pos);
    if (spin) tmp.want.applyAxisAngle(UP, state.clock.elapsedTime * 0.08 * s.offset);
    // engine running: a faint vibration when we're close to it
    if (s.engine > 0.5) tmp.want.addScalar(Math.sin(state.clock.elapsedTime * 55) * 0.004 * s.engine);
    cam.position.lerp(tmp.want, k);
    // on wide screens aim left of the car (exterior shots only) so it sits on the right, clear of the headline
    tmp.right.subVectors(s.target, cam.position).cross(UP).normalize();
    const off = state.size.width > 900 ? lookOffset * s.offset : 0;
    look.current.lerp(tmp.want.copy(s.target).addScaledVector(tmp.right, -off), k);
    cam.lookAt(look.current);
    if (Math.abs(cam.fov - s.fov) > 0.01) { cam.fov += (s.fov - cam.fov) * k; cam.updateProjectionMatrix(); }
    Object.assign(fx.current!, { explode: s.explode, wheel: s.wheel, pedal: s.pedal, hood: s.hood });
    engine.current = s.engine;
  });
  return null;
}

export function CarStage({ paint = "#b3121f", progress, interactive = false, spin = false, lookOffset = 0, className }:
  { paint?: string; progress?: MotionValue<number>; interactive?: boolean; spin?: boolean; lookOffset?: number; className?: string }) {
  const [anchors, setAnchors] = useState<Anchors | null>(null);
  const fx = useRef<CarFx>({ explode: 0, wheel: 0, pedal: 0, hood: 0 });
  const engine = useRef(0);
  const path = useMemo(() => (anchors ? buildShots(anchors) : null), [anchors]);
  return (
    <div className={className}>
      <Canvas shadows dpr={[1, 1.75]} camera={{ position: [5, 1.4, 6.5], fov: 30, near: 0.05 }}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.05 }}>
        <color attach="background" args={["#05060a"]} />
        <fog attach="fog" args={["#05060a", 10, 28]} />
        <Suspense fallback={null}>
          <HeroCar paint={paint} fx={fx} onAnchors={setAnchors} />
          {path && anchors && !interactive && (
            <>
              <EngineFx at={anchors.engine} forward={anchors.forward} visible={engine} />
            </>
          )}
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[60, 60]} />
            <MeshReflectorMaterial blur={[300, 90]} resolution={1024} mixBlur={1} mixStrength={12} roughness={0.9}
              depthScale={1} minDepthThreshold={0.4} maxDepthThreshold={1.2} color="#08090d" metalness={0.5} mirror={0.5} />
          </mesh>
          <ContactShadows position={[0, 0.004, 0]} opacity={0.8} scale={18} blur={2.2} far={3} />
          {/* studio light panels: no external HDR download */}
          <Environment resolution={512} frames={1} environmentIntensity={1.35}>
            <Lightformer intensity={2.6} position={[0, 7, 0]} rotation-x={Math.PI / 2} scale={[14, 4, 1]} />
            <Lightformer intensity={2} position={[-7, 2.5, 1]} rotation-y={Math.PI / 2} scale={[10, 2.4, 1]} color="#a8d4ff" />
            <Lightformer intensity={2} position={[7, 2.5, -1]} rotation-y={-Math.PI / 2} scale={[10, 2.4, 1]} color="#ffd6a8" />
            <Lightformer form="ring" intensity={5} position={[3, 4, 7]} scale={3} />
            <Lightformer intensity={1.2} position={[0, 1, -8]} scale={[16, 1.5, 1]} color="#ff6a3d" />
          </Environment>
          <spotLight position={[5, 9, 5]} angle={0.45} penumbra={1} intensity={80} castShadow shadow-mapSize={[2048, 2048]} />
          {/* cabin + bay fill so the interior and engine shots aren't black */}
          {anchors && <pointLight position={anchors.steering.clone().add(new THREE.Vector3(0, 0.5, 0))} intensity={3} distance={2.5} color="#ffe2c4" />}
          {anchors && <pointLight position={anchors.engine.clone().add(new THREE.Vector3(0, 0.9, 0))} intensity={4} distance={3} color="#cfe6ff" />}
        </Suspense>
        {interactive ? (
          <OrbitControls enablePan={false} minDistance={5} maxDistance={11} minPolarAngle={0.6} maxPolarAngle={1.5} target={[0, 0.55, 0]} autoRotate autoRotateSpeed={0.6} />
        ) : path ? (
          <Director progress={progress} shots={path.shots} spin={spin} lookOffset={lookOffset} fx={fx} engine={engine} />
        ) : null}
      </Canvas>
    </div>
  );
}
