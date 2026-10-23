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

export function HeroCar({ paint = "#b3121f", explode = 0, onReady }: { paint?: string; explode?: number; onReady?: (size: THREE.Vector3) => void }) {
  const { scene } = useGLTF(CAR_URL);
  const root = useMemo(() => scene.clone(true), [scene]);
  const explodeRef = useRef(explode);
  useEffect(() => { explodeRef.current = explode; }, [explode]);

  // Normalise size/position once and collect the parts that move in the exploded view
  const parts = useMemo(() => {
    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const scale = 4.6 / Math.max(size.x, size.z);
    root.scale.setScalar(scale);
    root.position.set(-center.x * scale, -box.min.y * scale, -center.z * scale);
    root.updateMatrixWorld(true);
    // The model's parts hang under one underbody node with a Z-up rotation: work out each move in world space,
    // then convert it into the part's own parent space so it travels in the intended direction.
    const lateral = size.x < size.z ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
    const base = root.getObjectByName("BodyUnderside") ?? root.children[0];
    const list: Part[] = [];
    for (const o of base?.children ?? []) {
      const n = o.name.toLowerCase();
      const wp = o.getWorldPosition(new THREE.Vector3());
      let world: THREE.Vector3 | null = null;
      if (n.startsWith("wheel")) {
        const side = Math.sign(wp.clone().sub(center.clone().multiplyScalar(0)).dot(lateral) || 1);
        world = lateral.clone().multiplyScalar(side * 0.85);                     // wheels slide out sideways
      } else if (n.startsWith("body") && !n.includes("underside")) {
        world = new THREE.Vector3(0, 1.25, 0);                                    // shell and doors lift away
      } else if (n.startsWith("engine")) {
        world = new THREE.Vector3(0, 0.45, 0);
      }
      if (!world || !o.parent) continue;
      const a = o.parent.worldToLocal(wp.clone());
      const b = o.parent.worldToLocal(wp.clone().add(world));
      list.push({ obj: o, base: o.position.clone(), dir: b.sub(a) });
    }
    onReady?.(size.multiplyScalar(scale));
    return list;
  }, [root, onReady]);

  // Paint: recolour every body-paint material, keeping its clearcoat / flake response
  useEffect(() => {
    const c = new THREE.Color(paint);
    root.traverse((o) => {
      const m = (o as THREE.Mesh).material as THREE.MeshPhysicalMaterial | undefined;
      if (m && m.name?.toLowerCase().startsWith("paint")) {
        const own = m.userData.__own ? m : m.clone();
        own.userData.__own = true;
        own.color.copy(c);
        // light paints read as pearl only with less metal; dark paints keep the deep metallic flake
        const light = c.r * 0.2126 + c.g * 0.7152 + c.b * 0.0722 > 0.55;
        own.metalness = light ? 0.25 : 0.7;
        own.roughness = light ? 0.32 : 0.28;
        own.clearcoat = 1;
        own.clearcoatRoughness = 0.04;
        (o as THREE.Mesh).material = own;
      }
      if ((o as THREE.Mesh).isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
  }, [root, paint]);

  useFrame((_, dt) => {
    for (const p of parts) {
      const target = p.base.clone().addScaledVector(p.dir, explodeRef.current);
      p.obj.position.lerp(target, 1 - Math.exp(-6 * dt));
    }
  });

  return <primitive object={root} />;
}

useGLTF.preload(CAR_URL);
