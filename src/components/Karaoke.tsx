import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import { COLORS } from "../lib";

// Word-by-word karaoke highlight, evenly distributed across the line's audio duration
export const Karaoke: React.FC<{ text: string; durationFrames: number; big?: boolean }> = ({
  text, durationFrames, big,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  const perWord = durationFrames / words.length;
  const enter = spring({ frame: f, fps, config: { damping: 12, stiffness: 160 } });
  return (
    <div
      style={{
        position: "absolute", bottom: 56, left: 0, right: 0,
        display: "flex", justifyContent: "center",
        transform: `translateY(${(1 - enter) * 80}px)`, opacity: enter,
      }}
    >
      <div
        style={{
          background: "rgba(255,255,255,0.94)", borderRadius: 32, padding: "22px 48px",
          maxWidth: 1560, display: "flex", flexWrap: "wrap", justifyContent: "center",
          gap: "0 16px", boxShadow: "0 10px 40px rgba(58,46,110,0.25)",
          border: `5px solid ${COLORS.sun}`,
        }}
      >
        {words.map((w, i) => {
          const active = f >= i * perWord && f < (i + 1) * perWord;
          const done = f >= (i + 1) * perWord;
          return (
            <span
              key={i}
              style={{
                fontSize: big ? 58 : 46, fontWeight: 800, lineHeight: 1.4,
                color: active ? COLORS.highlight : done ? COLORS.coral : COLORS.text,
                transform: active ? "scale(1.18)" : "scale(1)",
                display: "inline-block", transition: "none",
                textShadow: active ? "0 2px 0 rgba(0,0,0,0.08)" : undefined,
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
    </div>
  );
};
