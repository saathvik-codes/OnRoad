"use client";

// Concept car: "CarConcept" from the Khronos glTF Sample Assets, based on a CC0 model by Unity Fan,
// optimised by Eric Chadwick / Darmstadt Graphics Group, licensed CC-BY 4.0 (credit shown in the site footer).
// It is a generic showcase car, never presented as a specific manufacturer's model.

import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

export const CAR_URL = "/models/car-concept.glb";

type Part = { obj: THREE.Object3D; base: THREE.Vector3; dir: THREE.Vector3 };

/** World-space points the cinematic camera flies to (computed from the model, not guessed). */
export type Anchors = { steering: THREE.Vector3; engine: THREE.Vector3; forward: THREE.Vector3; size: THREE.Vector3; engineUnderHood: boolean };
/** Live animation values written by the director each frame. */
export type CarFx = { explode: number; wheel: number; pedal: number; hood: number };

const UP = new THREE.Vector3(0, 1, 0);

function center(o: THREE.Object3D) {
  return new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());
}

/** Wrap `objs` in a pivot placed at world point `at` (keeps their world transforms), so they can turn about it. */
function pivotAt(objs: THREE.Object3D[], at: THREE.Vector3) {
  const parent = objs[0]?.parent;
  if (!parent) return null;
  const pivot = new THREE.Object3D();
  pivot.name = objs[0].name + "Pivot";       // keeps the "Body…" prefix so the exploded view still lifts the bonnet
  parent.add(pivot);
  pivot.position.copy(parent.worldToLocal(at.clone()));
  pivot.updateMatrixWorld(true);
  for (const o of objs) pivot.attach(o);
  return pivot;
}

/** Axis given in world space, expressed in `obj`'s parent space (for rotating the pivot about it). */
function localAxis(obj: THREE.Object3D, worldAxis: THREE.Vector3) {
  const q = obj.parent!.getWorldQuaternion(new THREE.Quaternion()).invert();
  return worldAxis.clone().applyQuaternion(q).normalize();
}

export function HeroCar({ paint = "#b3121f", fx, onAnchors }: { paint?: string; fx: React.RefObject<CarFx>; onAnchors?: (a: Anchors) => void }) {
  const { scene } = useGLTF(CAR_URL);
  const root = useMemo(() => scene.clone(true), [scene]);

  const rig = useMemo(() => {
    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const mid = box.getCenter(new THREE.Vector3());
    const scale = 4.6 / Math.max(size.x, size.z);
    root.scale.setScalar(scale);
    root.position.set(-mid.x * scale, -box.min.y * scale, -mid.z * scale);
    root.updateMatrixWorld(true);

    const by = (n: string) => root.getObjectByName(n);
    const steeringParts = ["InteriorSteeringWheel01", "InteriorSteeringWheel02", "InteriorSteeringWheel03", "InteriorSteeringWheel04",
      "InteriorSteeringHandleL", "InteriorSteeringHandleR", "InteriorSteeringEmblem"].map(by).filter(Boolean) as THREE.Object3D[];
    const steering = steeringParts.length ? center(steeringParts[0]) : new THREE.Vector3(0, 1, 0);
    const engineObj = by("Engine");
    const engine = engineObj ? center(engineObj) : new THREE.Vector3();
    const lights = by("BodyHeadlights");
    // "forward" = from the car's centre towards its headlights, flattened to the ground
    const forward = (lights ? center(lights) : new THREE.Vector3(1, 0, 0)).setY(0).normalize();
    const hood = by("BodyHood");
    const hoodC = hood ? center(hood) : null;
    const engineUnderHood = !!hoodC && engine.distanceTo(hoodC) < engine.distanceTo(steering);

    // steering wheel turns about the column (roughly the car's forward axis, tilted)
    const wheelPivot = pivotAt(steeringParts, steering);
    const wheelAxis = wheelPivot ? localAxis(wheelPivot, forward.clone().add(new THREE.Vector3(0, 0.35, 0)).normalize()) : null;
    // bonnet hinges on its edge nearest the windscreen and lifts its front
    let hoodPivot: THREE.Object3D | null = null, hoodAxis: THREE.Vector3 | null = null;
    if (hood && hoodC) {
      const hb = new THREE.Box3().setFromObject(hood);
      const half = hb.getSize(new THREE.Vector3()).dot(new THREE.Vector3(Math.abs(forward.x), 0, Math.abs(forward.z))) / 2;
      const hinge = hoodC.clone().addScaledVector(forward, -half).setY(hb.max.y);
      const lids = ["BodyHood", "BodyHoodTopgrill", "BodyHoodUnder"].map(by).filter((o): o is THREE.Object3D => !!o && o.parent === hood.parent);
      hoodPivot = pivotAt(lids, hinge);
      if (hoodPivot) hoodAxis = localAxis(hoodPivot, new THREE.Vector3().crossVectors(forward, UP).normalize());
    }
    const pedal = ["InteriorPedalAccel", "InteriorPedalAccelArm"].map(by).filter(Boolean) as THREE.Object3D[];
    const pedalBase = pedal.map((p) => p.position.clone());
    const pedalDir = pedal.map((p) => p.parent!.worldToLocal(p.getWorldPosition(new THREE.Vector3()).addScaledVector(forward, 0.05).add(new THREE.Vector3(0, -0.02, 0)))
      .sub(p.position));

    // exploded view: wheels slide out, shell lifts, engine rises (same behaviour as before)
    const lateral = size.x < size.z ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
    const base = by("BodyUnderside") ?? root.children[0];
    const parts: Part[] = [];
    for (const o of base?.children ?? []) {
      const n = o.name.toLowerCase();
      const wp = o.getWorldPosition(new THREE.Vector3());
      let world: THREE.Vector3 | null = null;
      if (n.startsWith("wheel")) world = lateral.clone().multiplyScalar(Math.sign(wp.dot(lateral) || 1) * 0.85);
      else if (n.startsWith("body") && !n.includes("underside")) world = new THREE.Vector3(0, 1.25, 0);
      else if (n.startsWith("engine")) world = new THREE.Vector3(0, 0.45, 0);
      if (!world || !o.parent) continue;
      const a = o.parent.worldToLocal(wp.clone());
      const b = o.parent.worldToLocal(wp.clone().add(world));
      parts.push({ obj: o, base: o.position.clone(), dir: b.sub(a) });
    }
    return { parts, wheelPivot, wheelAxis, hoodPivot, hoodAxis, pedal, pedalBase, pedalDir,
             anchors: { steering, engine, forward, size: size.multiplyScalar(scale), engineUnderHood } as Anchors };
  }, [root]);

  useEffect(() => { onAnchors?.(rig.anchors); }, [rig, onAnchors]);

  // Paint: recolour every body-paint material, keeping its clearcoat / flake response
  useEffect(() => {
    const c = new THREE.Color(paint);
    root.traverse((o) => {
      const m = (o as THREE.Mesh).material as THREE.MeshPhysicalMaterial | undefined;
      if (m && m.name?.toLowerCase().startsWith("paint")) {
        const own = m.userData.__own ? m : m.clone();
        own.userData.__own = true;
        own.color.copy(c);
        const light = c.r * 0.2126 + c.g * 0.7152 + c.b * 0.0722 > 0.55;
        own.metalness = light ? 0.25 : 0.7;
        own.roughness = light ? 0.32 : 0.28;
        own.clearcoat = 1;
        own.clearcoatRoughness = 0.04;
        (o as THREE.Mesh).material = own;
      }
      if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; }
    });
  }, [root, paint]);

  const q = useMemo(() => new THREE.Quaternion(), []);
  useFrame((_, dt) => {
    const f = fx.current;
    if (!f) return;
    const k = 1 - Math.exp(-6 * dt);
    for (const p of rig.parts) p.obj.position.lerp(p.base.clone().addScaledVector(p.dir, f.explode), k);
    if (rig.wheelPivot && rig.wheelAxis) rig.wheelPivot.quaternion.slerp(q.setFromAxisAngle(rig.wheelAxis, f.wheel), k);
    if (rig.hoodPivot && rig.hoodAxis) rig.hoodPivot.quaternion.slerp(q.setFromAxisAngle(rig.hoodAxis, f.hood * 1.05), k);
    rig.pedal.forEach((p, i) => p.position.lerp(rig.pedalBase[i].clone().addScaledVector(rig.pedalDir[i], f.pedal), k));
  });

  return <primitive object={root} />;
}

useGLTF.preload(CAR_URL);
