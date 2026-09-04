import {
  AbsoluteFill, Audio, Img, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Baloo2";
import { timeline, INTRO, OUTRO, GAP, lineFrames, trackFrames, COLORS, FPS } from "./lib";
import { SceneBg } from "./components/SceneBg";
import { Character } from "./components/Character";
import { Particles } from "./components/Particles";
import { Karaoke } from "./components/Karaoke";

const { fontFamily } = loadFont();
const T = timeline.rhyme;

const TitleCard: React.FC<{ title: string }> = ({ title }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: f, fps, config: { damping: 10, stiffness: 120 } });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          transform: `scale(${pop}) rotate(${Math.sin(f / 10) * 2}deg)`,
          background: COLORS.card, borderRadius: 48, padding: "50px 90px",
          border: `10px solid ${COLORS.coral}`, boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
          maxWidth: 1400, textAlign: "center",
        }}
      >
        <div style={{ fontSize: 84, fontWeight: 800, color: COLORS.text, lineHeight: 1.15, textWrap: "balance" as never }}>
          {title.split("|")[0]}
        </div>
        <div style={{ fontSize: 44, fontWeight: 700, color: COLORS.highlight, marginTop: 14 }}>
          {title.split("|")[1] ?? ""}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Outro: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: f, fps, config: { damping: 9 } });
  const pulse = 1 + Math.sin((f / FPS) * Math.PI * 2 * 1.5) * 0.07;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 40 }}>
      <Character src={T.character} size={430} x={745} y={170} energy={1.3} />
      <div style={{ position: "absolute", bottom: 150, display: "flex", flexDirection: "column", alignItems: "center", gap: 24, transform: `scale(${pop})` }}>
        <div style={{ fontSize: 64, fontWeight: 800, color: COLORS.card, textShadow: "0 4px 12px rgba(0,0,0,0.35)" }}>
          Phir milenge! Bye bye!
        </div>
        <div
          style={{
            background: "#FF0000", color: "white", fontSize: 52, fontWeight: 800,
            padding: "20px 60px", borderRadius: 999, transform: `scale(${pulse})`,
            boxShadow: "0 10px 30px rgba(255,0,0,0.4)",
          }}
        >
          SUBSCRIBE karo!
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const RhymeVideo: React.FC = () => {
  let cursor = INTRO;
  const total = trackFrames(T);
  return (
    <AbsoluteFill style={{ fontFamily }}>
      <SceneBg />
      <Audio src={staticFile("assets/music.wav")} volume={0.34} loop />
      <Particles />
      <Sequence durationInFrames={INTRO}>
        <TitleCard title={T.title} />
      </Sequence>
      {T.lines.map((line, i) => {
        const from = cursor;
        const frames = lineFrames(line);
        cursor += frames;
        return (
          <Sequence key={i} from={from} durationInFrames={frames}>
            <Audio src={staticFile(line.audio)} volume={1} />
            {/* prop card bounces on the opposite side of the character */}
            <PropCard src={line.image} right={i % 2 === 0} />
            <Character src={T.character} size={560} x={i % 2 === 0 ? 130 : 1230} y={330} energy={1.15} flip={i % 2 !== 0} />
            <Karaoke text={line.text} durationFrames={frames - GAP} big />
          </Sequence>
        );
      })}
      <Sequence from={total - OUTRO} durationInFrames={OUTRO}>
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};

const PropCard: React.FC<{ src: string; right: boolean }> = ({ src, right }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: f, fps, config: { damping: 11, stiffness: 130 } });
  const bob = Math.sin((f / FPS) * Math.PI * 2 * 0.983) * 18;
  return (
    <div
      style={{
        position: "absolute", top: 200 + bob, left: right ? 1150 : 170,
        width: 480, height: 480, background: COLORS.card, borderRadius: 60,
        border: `10px solid ${COLORS.sun}`, boxShadow: "0 16px 50px rgba(0,0,0,0.22)",
        transform: `scale(${enter}) rotate(${Math.sin(f / 22) * 4}deg)`,
        overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center",
      }}
    >
      <Img src={staticFile(src)} style={{ width: "92%", height: "92%", objectFit: "contain" }} />
    </div>
  );
};
