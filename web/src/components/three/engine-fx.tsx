"use client";

// Cut-away engine effect shown when the camera dives into the engine bay: four pistons pumping in firing order
// (1-3-4-2), a glowing fuel rail with fuel pulses travelling to each injector, and a spark flash at each power stroke.
// Purely illustrative (it is not any manufacturer's engine).

import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

const ORDER = [0, Math.PI, Math.PI * 1.5, Math.PI * 0.5];   // phase offsets for cylinders 1..4 (firing order 1-3-4-2)

export function EngineFx({ at, forward, visible }: { at: THREE.Vector3; forward: THREE.Vector3; visible: React.RefObject<number> }) {
  const group = useRef<THREE.Group>(null);
  const pistons = useRef<THREE.Mesh[]>([]);
  const sparks = useRef<THREE.PointLight[]>([]);
  const fuel = useRef<THREE.InstancedMesh>(null);
  const yaw = Math.atan2(forward.x, forward.z);
  const tmp = useMemo(() => new THREE.Object3D(), []);
  const steel = useMemo(() => new THREE.MeshStandardMaterial({ color: "#c9ced8", metalness: 1, roughness: 0.22 }), []);
  const block = useMemo(() => new THREE.MeshStandardMaterial({ color: "#1b1f2a", metalness: 0.6, roughness: 0.45, transparent: true, opacity: 0.35 }), []);

  useFrame(({ clock }) => {
    const v = visible.current ?? 0;
    if (!group.current) return;
    group.current.visible = v > 0.02;
    group.current.scale.setScalar(THREE.MathUtils.lerp(0.4, 0.7, v));
    const t = clock.elapsedTime * 9;                               // engine speed
    pistons.current.forEach((p, i) => { if (p) p.position.y = 0.16 + Math.sin(t + ORDER[i]) * 0.09; });
    sparks.current.forEach((s, i) => { if (s) s.intensity = Math.max(0, Math.cos(t + ORDER[i])) ** 12 * 6 * v; });
    if (fuel.current) {
      for (let k = 0; k < 24; k++) {
        const x = ((clock.elapsedTime * 0.9 + k / 24) % 1) * 1.1 - 0.55;   // fuel droplets running along the rail
        tmp.position.set(x, 0.42, 0.12); tmp.scale.setScalar(0.018 + 0.01 * Math.sin(k)); tmp.updateMatrix();
        fuel.current.setMatrixAt(k, tmp.matrix);
      }
      fuel.current.instanceMatrix.needsUpdate = true;
    }
  });

  return (
    <group ref={group} position={at.clone().add(new THREE.Vector3(0, 0.12, 0))} rotation={[0, yaw + Math.PI / 2, 0]}>
      <mesh material={block} position={[0, 0.12, 0]}><boxGeometry args={[1.2, 0.34, 0.36]} /></mesh>
      {[0, 1, 2, 3].map((i) => (
        <group key={i} position={[-0.42 + i * 0.28, 0, 0]}>
          <mesh ref={(m) => { if (m) pistons.current[i] = m; }} material={steel}><cylinderGeometry args={[0.1, 0.1, 0.12, 24]} /></mesh>
          <pointLight ref={(l) => { if (l) sparks.current[i] = l; }} position={[0, 0.34, 0]} color="#7fd8ff" distance={0.8} intensity={0} />
          <mesh position={[0, 0.38, 0.12]}><cylinderGeometry args={[0.02, 0.02, 0.1, 10]} /><meshStandardMaterial color="#ffb347" emissive="#ff8a00" emissiveIntensity={1.4} /></mesh>
        </group>
      ))}
      {/* fuel rail */}
      <mesh position={[0, 0.42, 0.12]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.025, 0.025, 1.15, 12]} />
        <meshStandardMaterial color="#ff9a3d" emissive="#ff5a00" emissiveIntensity={0.9} transparent opacity={0.6} /></mesh>
      <instancedMesh ref={fuel} args={[undefined, undefined, 24]}>
        <sphereGeometry args={[1, 10, 10]} /><meshStandardMaterial color="#ffd27a" emissive="#ffb000" emissiveIntensity={2.4} />
      </instancedMesh>
    </group>
  );
}
