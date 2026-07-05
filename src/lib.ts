import timelineData from "./data/timeline.json";

export type Line = { text: string; image: string; audio: string; duration: number };
export type Track = { title: string; character: string; lines: Line[] };
export const timeline = timelineData as { rhyme: Track; story: Track };

export const FPS = 30;
export const INTRO = Math.round(2.5 * FPS);
export const OUTRO = Math.round(3.5 * FPS);
export const GAP = 8; // frames between lines

export const lineFrames = (l: Line) => Math.round(l.duration * FPS) + GAP;
export const trackFrames = (t: Track) =>
  INTRO + t.lines.reduce((a, l) => a + lineFrames(l), 0) + OUTRO;

// deterministic pseudo-random
export const rand = (seed: number) => {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

export const COLORS = {
  sky: "#8ED6FF",
  skyDeep: "#5DBBFF",
  sun: "#FFD93D",
  grass: "#7ED957",
  coral: "#FF6B6B",
  card: "#FFFFFF",
  text: "#3A2E6E",
  highlight: "#FF9F1C",
};
