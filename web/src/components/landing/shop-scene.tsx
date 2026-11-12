"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Component, useEffect, useMemo, useRef, type ReactNode } from "react";
import { type MotionValue } from "motion/react";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

type Vec = [number, number, number];
const palette = {
  green: "#285b45",
  mint: "#b4d2a5",
  cream: "#f5e9d1",
  peach: "#e5a278",
  clay: "#c87751",
  dark: "#233e32",
  yellow: "#edcb77",
};

function Box({
  position = [0, 0, 0],
  size = [1, 1, 1],
  color = palette.green,
  rotation = [0, 0, 0],
  radius = 0.035,
}: {
  position?: Vec;
  size?: Vec;
  color?: string;
  rotation?: Vec;
  radius?: number;
}) {
  const [width, height, depth] = size;
  const geometry = useMemo(
    () => new RoundedBoxGeometry(width, height, depth, 2, radius),
    [width, height, depth, radius],
  );
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <mesh
      geometry={geometry}
      position={position}
      rotation={rotation}
      castShadow
      receiveShadow
    >
      <meshStandardMaterial color={color} roughness={0.76} />
    </mesh>
  );
}

function Sign({
  text,
  small,
  position,
  size,
  color = palette.cream,
  background = palette.green,
}: {
  text: string;
  small?: string;
  position: Vec;
  size: [number, number];
  color?: string;
  background?: string;
}) {
  const texture = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 384;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, 1024, 384);
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "600 110px Trebuchet MS, sans-serif";
    ctx.fillText(text, 512, small ? 155 : 192);
    if (small) {
      ctx.font = "32px Trebuchet MS, sans-serif";
      ctx.fillText(small, 512, 270);
    }
    const result = new THREE.CanvasTexture(canvas);
    result.colorSpace = THREE.SRGBColorSpace;
    return result;
  }, [text, small, color, background]);
  useEffect(() => () => texture.dispose(), [texture]);
  return (
    <mesh position={position}>
      <planeGeometry args={size} />
      <meshBasicMaterial map={texture} toneMapped={false} />
    </mesh>
  );
}

function Fruit({
  position,
  color,
  scale = 0.1,
}: {
  position: Vec;
  color: string;
  scale?: number;
}) {
  return (
    <group position={position}>
      <mesh castShadow scale={[scale, scale * 0.9, scale]}>
        <sphereGeometry args={[1, 12, 10]} />
        <meshStandardMaterial color={color} roughness={0.8} />
      </mesh>
      <Box
        position={[0, scale, 0.01]}
        size={[0.025, 0.06, 0.025]}
        color={palette.green}
      />
    </group>
  );
}
function Crate({ position, color }: { position: Vec; color: string }) {
  return (
    <group position={position}>
      <Box size={[0.7, 0.15, 0.55]} color="#a97d54" />
      {[-0.27, 0.27].map((z) => (
        <Box
          key={z}
          position={[0, 0.15, z]}
          size={[0.74, 0.18, 0.045]}
          color="#bd9166"
        />
      ))}
      {[-0.34, 0.34].map((x) => (
        <Box
          key={x}
          position={[x, 0.15, 0]}
          size={[0.045, 0.18, 0.55]}
          color="#bd9166"
        />
      ))}
      {Array.from({ length: 6 }, (_, i) => (
        <Fruit
          key={i}
          position={[((i % 3) - 1) * 0.2, 0.16, i < 3 ? -0.12 : 0.1]}
          color={color}
        />
      ))}
    </group>
  );
}

function Carton({
  position,
  rotation = [0, 0, 0],
  scale = 1,
}: {
  position: Vec;
  rotation?: Vec;
  scale?: number;
}) {
  return (
    <group position={position} rotation={rotation} scale={scale}>
      <Box size={[0.39, 0.65, 0.33]} color="#f4eddb" />
      <Box
        position={[0, 0.08, 0.172]}
        size={[0.31, 0.2, 0.012]}
        color={palette.green}
        radius={0.005}
      />
      <Sign text="OAT" position={[0, 0.085, 0.181]} size={[0.27, 0.11]} />
      <mesh position={[0, 0.385, 0]} rotation={[0, 0, Math.PI / 4]} castShadow>
        <boxGeometry args={[0.275, 0.275, 0.32]} />
        <meshStandardMaterial color="#e4d5b7" />
      </mesh>
      <Box
        position={[0, 0.57, 0]}
        size={[0.39, 0.035, 0.06]}
        color={palette.green}
      />
    </group>
  );
}

function Bag({
  position,
  rotation = [0, 0, 0],
  scale = 1,
}: {
  position: Vec;
  rotation?: Vec;
  scale?: number;
}) {
  return (
    <group position={position} rotation={rotation} scale={scale}>
      <Box size={[0.64, 0.74, 0.38]} color="#d9ad74" />
      <mesh position={[0, 0.42, 0]} castShadow>
        <torusGeometry args={[0.19, 0.025, 8, 28, Math.PI]} />
        <meshStandardMaterial color="#855d3e" />
      </mesh>
      <mesh position={[0, 0, 0.201]}>
        <circleGeometry args={[0.15, 32]} />
        <meshBasicMaterial color={palette.green} />
      </mesh>
      <Sign text="KF" position={[0, 0, 0.206]} size={[0.21, 0.13]} />
      <Fruit position={[-0.16, 0.39, 0]} color="#c3784e" scale={0.12} />
      <mesh
        position={[0.13, 0.44, 0]}
        rotation={[0, 0, -0.3]}
        scale={[0.14, 0.32, 0.1]}
      >
        <sphereGeometry args={[1, 12, 12]} />
        <meshStandardMaterial color="#759763" />
      </mesh>
    </group>
  );
}

function Shop({ progress }: { progress: MotionValue<number> }) {
  const door = useRef<THREE.Group>(null);
  const roof = useRef<THREE.Group>(null);
  useFrame(() => {
    const p = progress.get();
    if (door.current) door.current.rotation.y = -Math.min(1, p * 4) * 1.05;
    if (roof.current)
      roof.current.position.y = Math.sin(Math.min(1, p * 2) * Math.PI) * 0.22;
  });
  return (
    <group>
      <Box
        position={[0, -0.12, 0]}
        size={[5, 0.24, 3.6]}
        color="#e1d3b9"
        radius={0.12}
      />
      <Box position={[0, 0.02, 0.2]} size={[4.3, 0.1, 2.8]} color="#d9c7a6" />
      <Box
        position={[0, 1.5, -0.5]}
        size={[3.8, 3, 1.7]}
        color={palette.cream}
        radius={0.09}
      />
      <Box
        position={[0, 2.95, -0.5]}
        size={[4.08, 0.18, 1.95]}
        color="#e2c59c"
        radius={0.06}
      />
      <Box
        position={[0, 0.15, 0.42]}
        size={[3.9, 0.25, 0.28]}
        color={palette.green}
      />
      {/* Framed glass shopfront, deliberately built from lightweight geometry. */}
      {[-1.18, 1.18].map((x) => (
        <group key={x}>
          <Box
            position={[x, 1.18, 0.37]}
            size={[1.16, 1.85, 0.14]}
            color={palette.green}
          />
          <Box
            position={[x, 1.22, 0.455]}
            size={[0.96, 1.53, 0.025]}
            color="#a8bdb0"
          />
          <Box
            position={[x - 0.27, 1.42, 0.48]}
            size={[0.025, 1.02, 0.01]}
            color="#d6e2d8"
          />
          <Box
            position={[x, 1, 0.49]}
            size={[1.02, 0.06, 0.035]}
            color={palette.green}
          />
        </group>
      ))}
      <Box
        position={[0, 1.05, 0.38]}
        size={[0.92, 2.02, 0.14]}
        color="#16382b"
      />
      <group ref={door} position={[-0.43, 0.08, 0.49]}>
        <Box
          position={[0.43, 0.95, 0]}
          size={[0.84, 1.9, 0.09]}
          color={palette.green}
        />
        <Box
          position={[0.43, 1.16, 0.06]}
          size={[0.66, 1.14, 0.02]}
          color="#afc9bb"
        />
        <Box
          position={[0.75, 0.94, 0.1]}
          size={[0.035, 0.27, 0.04]}
          color="#dfbc79"
        />
      </group>
      <group ref={roof}>
        <Box
          position={[0, 2.62, 0.39]}
          size={[3.55, 0.58, 0.14]}
          color={palette.green}
        />
        <Sign
          text="Kampung Fresh"
          small="YOUR NEIGHBOURHOOD GROCER"
          position={[0, 2.63, 0.472]}
          size={[3.3, 0.53]}
        />
        {Array.from({ length: 10 }, (_, i) => (
          <group key={i}>
            <Box
              position={[-1.71 + i * 0.38, 2.15, 0.85]}
              size={[0.39, 0.1, 1.16]}
              rotation={[0.24, 0, 0]}
              color={i % 2 ? "#f1e4c9" : palette.green}
            />
            <Box
              position={[-1.71 + i * 0.38, 1.94, 1.4]}
              size={[0.39, 0.25, 0.08]}
              color={i % 2 ? "#f1e4c9" : palette.green}
              radius={0.07}
            />
          </group>
        ))}
      </group>
      <Box
        position={[-1.32, 0.41, 1.02]}
        size={[1.0, 0.64, 0.64]}
        color="#b59166"
      />
      <Crate position={[-1.31, 0.76, 1.03]} color="#d78d4c" />
      <Crate position={[1.36, 0.26, 1.04]} color="#8aa76b" />
      <Carton position={[-1.4, 1.25, 0.53]} scale={0.55} />
      <Carton position={[-1.01, 1.25, 0.53]} scale={0.55} />
      <Bag position={[0.65, 0.43, 1.25]} scale={0.75} />
      <group position={[2.13, 0.35, 0.67]}>
        <mesh castShadow>
          <cylinderGeometry args={[0.22, 0.16, 0.44, 16]} />
          <meshStandardMaterial color="#bd795a" />
        </mesh>
        {[-0.15, 0, 0.15].map((x, i) => (
          <mesh
            key={i}
            position={[x, 0.49 + i * 0.06, 0]}
            rotation={[0, 0, x * 2]}
            scale={[0.13, 0.5, 0.13]}
            castShadow
          >
            <sphereGeometry args={[1, 12, 12]} />
            <meshStandardMaterial color={i === 1 ? "#537d51" : "#7c9c63"} />
          </mesh>
        ))}
      </group>
      <Box
        position={[-2.05, 0.67, 1.1]}
        size={[0.52, 0.93, 0.07]}
        rotation={[-0.13, 0, -0.04]}
        color={palette.green}
      />
      <Sign
        text="HELLO!"
        small="COME ON IN"
        position={[-2.05, 0.7, 1.17]}
        size={[0.46, 0.43]}
      />
    </group>
  );
}

function Person({
  position,
  green = false,
}: {
  position: Vec;
  green?: boolean;
}) {
  return (
    <group position={position}>
      <mesh position={[0, 0.57, 0]} castShadow>
        <sphereGeometry args={[0.145, 16, 12]} />
        <meshStandardMaterial color={green ? "#b7d799" : "#d5b89b"} />
      </mesh>
      <mesh position={[0, 0.26, 0]} castShadow>
        <capsuleGeometry args={[0.15, 0.24, 4, 12]} />
        <meshStandardMaterial color={green ? palette.green : "#b4afa1"} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
        <ringGeometry args={[0.25, 0.275, 32]} />
        <meshBasicMaterial
          color={green ? "#88b676" : "#c9bfaf"}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
}

function World({
  progress,
  hero,
}: {
  progress: MotionValue<number>;
  hero: boolean;
}) {
  const group = useRef<THREE.Group>(null),
    people = useRef<THREE.Group>(null),
    chart = useRef<THREE.Group>(null);
  const { invalidate, size, camera } = useThree();
  useEffect(
    () => progress.on("change", () => invalidate()),
    [progress, invalidate],
  );
  useFrame(() => {
    const p = progress.get();
    if (group.current) {
      group.current.rotation.y =
        (hero ? -0.48 : -0.45) + p * (hero ? 0.35 : 1.1);
      group.current.position.x = hero ? 0 : p < 0.5 ? -0.2 : -(p - 0.5) * 1.8;
      group.current.scale.setScalar(hero ? 1 : 1 - p * 0.12);
    }
    if (people.current) {
      people.current.visible = !hero && p > 0.23;
      people.current.scale.setScalar(
        Math.max(0.001, Math.min(1, (p - 0.23) * 6)),
      );
    }
    if (chart.current) {
      chart.current.visible = !hero && p > 0.65;
      chart.current.scale.y = Math.max(0.001, Math.min(1, (p - 0.65) * 4));
    }
    camera.position.set(
      0,
      hero ? 4.3 : 4.9,
      hero ? (size.width < 600 ? 10.7 : 9.2) : size.width < 600 ? 13.2 : 11.8,
    );
    camera.lookAt(0, 1.2, 0);
  });
  return (
    <>
      <ambientLight intensity={1.9} />
      <hemisphereLight args={["#fff9ea", "#d4c5a7", 1.8]} />
      <directionalLight
        castShadow
        position={[-4, 8, 5]}
        intensity={3.2}
        shadow-mapSize={[1024, 1024]}
        shadow-camera-left={-7}
        shadow-camera-right={7}
        shadow-camera-top={7}
        shadow-camera-bottom={-7}
        shadow-normalBias={0.04}
      />
      <group ref={group} position={[0, 0, 0]}>
        <Shop progress={progress} />
      </group>
      <group ref={people} visible={false}>
        {Array.from({ length: 7 }, (_, i) => (
          <Person
            key={i}
            position={[-3.2 + i * 1.04, 0.02, 2.7 + Math.sin(i) * 0.25]}
            green={i === 2 || i === 3 || i === 5}
          />
        ))}
      </group>
      <group ref={chart} position={[2.35, 0, 1.3]} visible={false}>
        <Box
          position={[0, 0.48, 0]}
          size={[0.45, 0.96, 0.45]}
          color="#baad93"
        />
        <Box
          position={[0.68, 0.91, 0]}
          size={[0.45, 1.82, 0.45]}
          color={palette.green}
        />
        <Sign
          text="30%"
          position={[0, 0.22, 0.24]}
          size={[0.38, 0.16]}
          background="#baad93"
        />
        <Sign text="57%" position={[0.68, 0.3, 0.24]} size={[0.38, 0.16]} />
      </group>
      <mesh
        receiveShadow
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.26, 0]}
      >
        <planeGeometry args={[200, 200]} />
        <shadowMaterial transparent opacity={0.16} />
      </mesh>
    </>
  );
}

class SceneBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

export default function ShopScene({
  progress,
  hero = false,
  fallback,
}: {
  progress: MotionValue<number>;
  hero?: boolean;
  fallback: ReactNode;
}) {
  return (
    <SceneBoundary fallback={fallback}>
      <Canvas
        aria-hidden="true"
        shadows={{ type: THREE.PCFShadowMap }}
        frameloop="demand"
        dpr={[1, 1.5]}
        camera={{ position: [0, 4.3, 9.2], fov: 38 }}
        gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
        fallback={fallback}
      >
        <World progress={progress} hero={hero} />
      </Canvas>
    </SceneBoundary>
  );
}
