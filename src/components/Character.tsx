import { Img, staticFile, useCurrentFrame } from "remotion";
import { FPS } from "../lib";

// Beat-synced dancing sticker: bounce + squash/stretch + sway (118 BPM)
export const Character: React.FC<{
  src: string; size: number; x?: number; y?: number; energy?: number; flip?: boolean;
}> = ({ src, size, x = 0, y = 0, energy = 1, flip }) => {
  const f = useCurrentFrame();
  const beatHz = 118 / 60;
  const ph = (f / FPS) * beatHz * Math.PI * 2;
  const bounce = Math.abs(Math.sin(ph)) * 34 * energy;
  const squash = 1 + Math.sin(ph * 2) * 0.06 * energy;
  const sway = Math.sin(ph / 2) * 7 * energy;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: size, height: size }}>
      <div
        style={{
          width: "100%", height: "100%",
          transform: `translateY(${-bounce}px) rotate(${sway}deg) scale(${(flip ? -1 : 1) * (2 - squash)}, ${squash})`,
          transformOrigin: "bottom center",
        }}
      >
        <Img
          src={staticFile(src)}
          style={{ width: "100%", height: "100%", objectFit: "contain", mixBlendMode: "multiply" }}
        />
      </div>
      <div
        style={{
          position: "absolute", bottom: -12, left: "18%", width: "64%", height: 26,
          borderRadius: "50%", background: "rgba(30,60,30,0.25)",
          transform: `scale(${1 - bounce / 220})`, filter: "blur(6px)",
        }}
      />
    </div>
  );
};
