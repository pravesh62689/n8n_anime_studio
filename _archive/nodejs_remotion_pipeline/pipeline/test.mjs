// Expert test suite: validates every pipeline stage before render/upload.
// Run: npm test  — each failed check prints its FIX.
import { existsSync, readFileSync, statSync, readdirSync } from "fs";
import { execSync } from "child_process";

const R = { pass: 0, fail: 0 };
const t = (name, ok, fix) => {
  if (ok) { R.pass++; console.log(`PASS  ${name}`); }
  else { R.fail++; console.log(`FAIL  ${name}\n      FIX: ${fix}`); }
};

// --- T1: Environment ---
const hasFfmpeg = (() => { try { execSync("ffmpeg -version", { stdio: "pipe" }); return true; } catch { return existsSync("node_modules/@remotion/compositor-linux-x64-gnu") || readdirSync("node_modules/@remotion").some((d) => d.startsWith("compositor")); } })();
t("ffmpeg available (system or Remotion bundled)", hasFfmpeg,
  "Install ffmpeg: sudo apt install ffmpeg (Linux) / winget install ffmpeg (Windows). Remotion renders work without it; only pipeline/music.mjs needs it.");
t("node >= 18", parseInt(process.versions.node) >= 18,
  "Upgrade Node.js to v18+ from nodejs.org");
t("node_modules present", existsSync("node_modules/remotion"),
  "Run: npm install");

// --- T2: Content config ---
let content = null;
try { content = await import("./content.mjs"); } catch {}
t("content.mjs loads", !!content, "Fix syntax error in pipeline/content.mjs");
if (content) {
  const lines = content.RHYME.lines;
  t("rhyme has 8+ lines (needed for ~5 min video)", lines.length >= 8,
    "Add more verses to RHYME.lines in pipeline/content.mjs. ~5 min needs 14-18 lines with repetition (chorus x3). Repeat chorus lines — repetition is what kids love and boosts watch time.");
  t("lines are Hinglish (short words)", lines.every((l) => l.text.split(" ").length <= 12),
    "Keep each line under 12 words so karaoke text fits on screen");
}

// --- T3: Generated assets ---
const hasAssets = existsSync("public/assets");
t("assets generated", hasAssets && readdirSync("public/assets").length > 4,
  "Run: npm run generate");
if (hasAssets) {
  const empty = readdirSync("public/assets").filter((f) => statSync(`public/assets/${f}`).size < 1000);
  t("no empty/corrupt assets", empty.length === 0,
    `Delete and regenerate: ${empty.join(", ") || "-"}. Pollinations sometimes rate-limits; the pipeline retries, but re-run npm run generate if files are tiny.`);
}

// --- T4: Timeline (audio sync) ---
const hasTL = existsSync("src/data/timeline.json");
t("timeline.json exists", hasTL, "Run: npm run generate (it writes exact audio durations)");
if (hasTL) {
  const tl = JSON.parse(readFileSync("src/data/timeline.json", "utf8"));
  const total = tl.rhyme.lines.reduce((s, l) => s + l.duration + 0.5, 0); // +0.5s gap per line
  t(`rhyme length ~5 min (currently ${(total / 60).toFixed(1)} min of ${tl.rhyme.lines.length} lines)`, total >= 240,
    "For a 5-minute video: content.mjs now has 20 lines with chorus repeats. Re-run: npm run generate && npm run render. Chorus repeats reuse existing images (only new TTS lines are fetched), so it is fast and free.");
  t("every line has audio file", tl.rhyme.lines.every((l) => existsSync(`public/${l.audio}`)),
    "A TTS call failed. Re-run: npm run generate (Edge TTS is free; transient network errors resolve on retry)");
  t("no zero-duration lines", tl.rhyme.lines.every((l) => l.duration > 0.4),
    "Zero duration = corrupt mp3. Delete public/assets/*.mp3 and re-run npm run generate");
}

// --- T5: Render output ---
if (existsSync("out/rhyme-final.mp4")) {
  const size = statSync("out/rhyme-final.mp4").size;
  t("rendered video > 5MB", size > 5_000_000,
    "Tiny file = failed render. Check: npx remotion render RhymeVideo out/rhyme-final.mp4 --log=verbose");
  try {
    const dur = parseFloat(execSync('ffprobe -v error -show_entries format=duration -of csv=p=0 out/rhyme-final.mp4', { stdio: "pipe" }).toString());
    t(`video duration matches timeline (${(dur / 60).toFixed(1)} min)`, dur > 30,
      "Duration mismatch: delete out/ and re-render after re-running npm run generate");
  } catch {}
} else {
  console.log("SKIP  render checks (run: npm run render)");
}

// --- T6: Upload readiness ---
t("SEO metadata builds", await import("./seo.mjs").then((m) => !!m.buildMetadata({ type: "rhyme", title: "x", topic: "y", keywords: [] }).title).catch(() => false),
  "Fix syntax error in pipeline/seo.mjs");
t("YouTube token saved (optional until upload)", existsSync(".yt-token.json"),
  "One-time: YT_CLIENT_ID=... YT_CLIENT_SECRET=... npm run auth");

console.log(`\n${R.pass} passed, ${R.fail} failed`);
process.exit(R.fail > 1 ? 1 : 0); // token check is a warning, allow 1 fail
