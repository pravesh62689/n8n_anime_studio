// FREE asset pipeline: Pollinations AI (images) + MS Edge TTS (voice) + synthesized music.
import fs from "node:fs";
import path from "node:path";
import { Readable } from "node:stream";
import { pipeline as streamPipe } from "node:stream/promises";
import { MsEdgeTTS, OUTPUT_FORMAT } from "msedge-tts";
import { parseFile } from "music-metadata";
import { RHYME, STORY, STYLE } from "./content.mjs";
import { makeMusic } from "./music.mjs";

const ROOT = path.resolve(import.meta.dirname, "..");
const ASSETS = path.join(ROOT, "public", "assets");
fs.mkdirSync(ASSETS, { recursive: true });
fs.mkdirSync(path.join(ROOT, "src", "data"), { recursive: true });

const imgUrl = (prompt, w, h, seed) =>
  `https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?width=${w}&height=${h}&seed=${seed}&nologo=true&model=flux&enhance=false`;

async function download(url, dest, tries = 3) {
  if (fs.existsSync(dest) && fs.statSync(dest).size > 5000) return console.log(`[skip] ${path.basename(dest)}`);
  for (let i = 0; i < tries; i++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(120000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const buf = Buffer.from(await res.arrayBuffer());
      if (buf.length < 5000) throw new Error("too small");
      fs.writeFileSync(dest, buf);
      return console.log(`[img] ${path.basename(dest)} (${(buf.length / 1024) | 0}kb)`);
    } catch (e) {
      console.log(`[retry ${i + 1}] ${path.basename(dest)}: ${e.message}`);
      await new Promise((r) => setTimeout(r, 4000 * (i + 1)));
    }
  }
  throw new Error(`Failed image: ${dest}`);
}

async function tts(text, voice, opts, dest) {
  if (fs.existsSync(dest) && fs.statSync(dest).size > 1000) {
    console.log(`[skip] ${path.basename(dest)}`);
  } else {
    const t = new MsEdgeTTS();
    await t.setMetadata(voice, OUTPUT_FORMAT.AUDIO_24KHZ_96KBITRATE_MONO_MP3);
    const { audioStream } = t.toStream(text, opts);
    await streamPipe(Readable.fromWeb ? audioStream : audioStream, fs.createWriteStream(dest));
    console.log(`[tts] ${path.basename(dest)}`);
  }
  const meta = await parseFile(dest);
  return meta.format.duration ?? 2;
}

async function build(content, kind) {
  const seedBase = kind === "rhyme" ? 41 : 91;
  // character sprite
  const charFile = `${content.character.key}.jpg`;
  await download(imgUrl(content.character.prompt, 768, 768, seedBase), path.join(ASSETS, charFile));

  const lines = [];
  const seen = new Set();
  for (let i = 0; i < content.lines.length; i++) {
    const L = content.lines[i];
    const key = L.prop ?? L.scene;
    const file = `${kind}-${key}.jpg`;
    if (!seen.has(key) && (L.propPrompt || L.scenePrompt)) {
      seen.add(key);
      const prompt = L.propPrompt
        ? `${L.propPrompt}, ${STYLE}, isolated on pure white background, sticker`
        : `${L.scenePrompt}, ${STYLE}, wide cinematic shot`;
      const [w, h] = L.propPrompt ? [640, 640] : [1280, 720];
      await download(imgUrl(prompt, w, h, seedBase + i + 1), path.join(ASSETS, file));
    }
    const audioFile = `${kind}-line-${i}.mp3`;
    const duration = await tts(L.text, content.voice, content.ttsOpts, path.join(ASSETS, audioFile));
    lines.push({ text: L.text, image: file, audio: `assets/${audioFile}`, duration });
  }
  return { title: content.title, character: `assets/${charFile}`, lines: lines.map((l) => ({ ...l, image: `assets/${l.image}` })) };
}

console.log("=== FREE ASSET PIPELINE ===");
makeMusic(path.join(ASSETS, "music.wav"));
console.log("[music] music.wav synthesized");

const rhyme = await build(RHYME, "rhyme");
const story = await build(STORY, "story");

fs.writeFileSync(path.join(ROOT, "src", "data", "timeline.json"), JSON.stringify({ rhyme, story }, null, 2));
console.log("=== DONE: src/data/timeline.json written ===");
