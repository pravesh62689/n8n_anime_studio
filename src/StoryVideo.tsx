import {
  AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Baloo2";
import { timeline, INTRO, OUTRO, GAP, lineFrames, trackFrames, COLORS } from "./lib";
import { Character } from "./components/Character";
import { Particles } from "./components/Particles";
import { SceneBg } from "./components/SceneBg";

const { fontFamily } = loadFont();
const T = timeline.story;

const Scene: React.FC<{ src: string; frames: number; zoomIn: boolean }> = ({ src, frames, zoomIn }) => {
  const f = useCurrentFrame();
  const scale = interpolate(f, [0, frames], zoomIn ? [1.02, 1.16] : [1.16, 1.02]);
  const pan = interpolate(f, [0, frames], zoomIn ? [-20, 20] : [20, -20]);
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img
        src={staticFile(src)}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale}) translateX(${pan}px)` }}
      />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(30,10,60,0.45)" }} />
    </AbsoluteFill>
  );
};

const Subtitle: React.FC<{ text: string }> = ({ text }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: f, fps, config: { damping: 13 } });
  return (
    <div
      style={{
        position: "absolute", bottom: 60, left: 0, right: 0, display: "flex", justifyContent: "center",
        opacity: enter, transform: `translateY(${(1 - enter) * 60}px)`,
      }}
    >
      <div
        style={{
          background: "rgba(20,12,50,0.78)", borderRadius: 28, padding: "22px 50px",
          maxWidth: 1500, fontSize: 50, fontWeight: 700, color: "white",
          textAlign: "center", lineHeight: 1.4, border: "4px solid rgba(255,217,61,0.85)",
        }}
      >
        {text}
      </div>
    </div>
  );
};

export const StoryVideo: React.FC = () => {
  let cursor = INTRO;
  const total = trackFrames(T);
  return (
    <AbsoluteFill style={{ fontFamily, background: "#1a1440" }}>
      <Audio src={staticFile("assets/music.wav")} volume={0.14} loop />
      <Sequence durationInFrames={INTRO}>
        <SceneBg hue={20} />
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div
            style={{
              background: COLORS.card, borderRadius: 48, padding: "50px 90px", textAlign: "center",
              border: `10px solid ${COLORS.highlight}`, maxWidth: 1400,
            }}
          >
            <div style={{ fontSize: 80, fontWeight: 800, color: COLORS.text, lineHeight: 1.15 }}>
              {T.title.split("|")[0]}
            </div>
            <div style={{ fontSize: 42, fontWeight: 700, color: COLORS.coral, marginTop: 12 }}>
              {T.title.split("|")[1] ?? ""}
            </div>
          </div>
        </AbsoluteFill>
      </Sequence>
      {T.lines.map((line, i) => {
        const from = cursor;
        const frames = lineFrames(line);
        cursor += frames;
        return (
          <Sequence key={i} from={from} durationInFrames={frames}>
            <Scene src={line.image} frames={frames} zoomIn={i % 2 === 0} />
            <Audio src={staticFile(line.audio)} volume={1} />
            <Character src={T.character} size={330} x={i % 2 === 0 ? 90 : 1500} y={620} energy={0.5} flip={i % 2 !== 0} />
            <Subtitle text={line.text} />
          </Sequence>
        );
      })}
      <Sequence from={total - OUTRO} durationInFrames={OUTRO}>
        <SceneBg hue={-15} />
        <Particles count={10} />
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 30 }}>
          <div style={{ fontSize: 70, fontWeight: 800, color: COLORS.text, background: COLORS.card, padding: "26px 70px", borderRadius: 40, border: `8px solid ${COLORS.coral}` }}>
            The End! SUBSCRIBE karo!
          </div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
