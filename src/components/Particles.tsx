import { AbsoluteFill, useCurrentFrame } from "remotion";
import { rand } from "../lib";

const GLYPHS = ["\u266A", "\u266B", "\u2726", "\u2665", "\u2605"];
const HUES = ["#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF", "#FF9F1C"];

export const Particles: React.FC<{ count?: number }> = ({ count = 14 }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: count }).map((_, i) => {
        const speed = 1 + rand(i) * 1.6;
        const yy = 1180 - ((f * speed + rand(i + 3) * 1200) % 1300);
        const xx = rand(i + 7) * 1820 + Math.sin(f / 25 + i) * 40;
        return (
          <div
            key={i}
            style={{
              position: "absolute", left: xx, top: yy,
              fontSize: 30 + rand(i + 11) * 34, color: HUES[i % HUES.length],
              opacity: 0.85, transform: `rotate(${Math.sin(f / 18 + i) * 25}deg)`,
              textShadow: "0 2px 6px rgba(0,0,0,0.15)",
            }}
          >
            {GLYPHS[i % GLYPHS.length]}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
