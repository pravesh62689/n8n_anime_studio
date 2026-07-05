import { AbsoluteFill, useCurrentFrame } from "remotion";
import { COLORS, rand } from "../lib";

export const SceneBg: React.FC<{ hue?: number }> = ({ hue = 0 }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ filter: hue ? `hue-rotate(${hue}deg)` : undefined }}>
      <AbsoluteFill
        style={{ background: `linear-gradient(180deg, ${COLORS.sky} 0%, ${COLORS.skyDeep} 55%, #C9F2FF 100%)` }}
      />
      {/* sun with rotating rays */}
      <div style={{ position: "absolute", top: 60, right: 100 }}>
        <div
          style={{
            position: "absolute", inset: -55, borderRadius: "50%",
            background: `conic-gradient(${Array.from({ length: 24 })
              .map((_, i) => `${i % 2 ? "transparent" : COLORS.sun + "55"} ${i * 15}deg ${(i + 1) * 15}deg`)
              .join(",")})`,
            transform: `rotate(${f * 0.4}deg)`,
          }}
        />
        <div style={{ width: 130, height: 130, borderRadius: "50%", background: COLORS.sun, boxShadow: `0 0 60px ${COLORS.sun}` }} />
      </div>
      {/* drifting clouds */}
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            top: 60 + rand(i) * 220,
            left: ((f * (0.6 + rand(i + 9) * 0.7) + rand(i + 5) * 1900) % 2200) - 300,
            display: "flex", alignItems: "flex-end", opacity: 0.9,
          }}
        >
          {[70, 100, 65].map((s, j) => (
            <div key={j} style={{ width: s * (1 + rand(i) * 0.5), height: s * 0.7 * (1 + rand(i) * 0.5), background: "white", borderRadius: 999, marginLeft: -22 }} />
          ))}
        </div>
      ))}
      {/* rolling hills */}
      <div style={{ position: "absolute", bottom: -140, left: -200, width: 1400, height: 460, borderRadius: "50%", background: "#8FE06A" }} />
      <div style={{ position: "absolute", bottom: -190, right: -250, width: 1500, height: 480, borderRadius: "50%", background: COLORS.grass }} />
    </AbsoluteFill>
  );
};
