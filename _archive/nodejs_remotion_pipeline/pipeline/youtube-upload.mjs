// Automated YouTube uploader with SEO metadata + peak-time scheduling.
// Run: npm run upload
// Uploads every .mp4 in out/ as PRIVATE with a scheduled publishAt at the next
// peak IST slots (8AM / 1PM / 6PM) — 3 per day. YouTube auto-publishes them.
// Requires .yt-token.json (run: node pipeline/youtube-auth.mjs once first).

import { google } from "googleapis";
import { createReadStream, readFileSync, existsSync, readdirSync } from "node:fs";
import { buildMetadata, nextPeakTimes } from "./seo.mjs";
import { RHYME, STORY } from "./content.mjs";

const { YT_CLIENT_ID, YT_CLIENT_SECRET } = process.env;
if (!existsSync(".yt-token.json") || !YT_CLIENT_ID) {
  console.error("Missing auth. First: set YT_CLIENT_ID/YT_CLIENT_SECRET and run `node pipeline/youtube-auth.mjs`");
  process.exit(1);
}

const oauth2 = new google.auth.OAuth2(YT_CLIENT_ID, YT_CLIENT_SECRET);
oauth2.setCredentials(JSON.parse(readFileSync(".yt-token.json", "utf8")));
const yt = google.youtube({ version: "v3", auth: oauth2 });

const videos = readdirSync("out").filter((f) => f.endsWith(".mp4"));
if (!videos.length) { console.error("No .mp4 files in out/. Render first."); process.exit(1); }

const slots = nextPeakTimes(videos.length);

let uploaded = 0;
let failed = 0;

for (let i = 0; i < videos.length; i++) {
  const file = videos[i];
  const isRhyme = file.includes("rhyme");
  const src = isRhyme ? RHYME : STORY;
  const meta = buildMetadata({
    type: isRhyme ? "rhyme" : "story",
    title: src.title,
    topic: src.topic ?? src.title,
    keywords: src.keywords ?? [],
  });

  console.log(`Uploading ${file} -> "${meta.title}" (publishes ${slots[i]} UTC)`);
  try {
    const res = await yt.videos.insert({
      part: ["snippet", "status"],
      requestBody: {
        snippet: {
          title: meta.title,
          description: meta.description,
          tags: meta.tags,
          categoryId: meta.categoryId,
          defaultLanguage: meta.defaultLanguage,
          defaultAudioLanguage: "hi",
        },
        status: {
          privacyStatus: "private",
          publishAt: slots[i],           // auto-publishes at peak IST time
          selfDeclaredMadeForKids: true, // REQUIRED for kids' content (COPPA)
        },
      },
      media: { body: createReadStream(`out/${file}`) },
    });
    console.log(`  Done: https://youtube.com/watch?v=${res.data.id}`);
    uploaded++;
  } catch (err) {
    failed++;
    console.error(`  FAILED: ${file} — ${err.message ?? err}`);
    if (err.code === 403) {
      console.error("  YouTube API quota may be exhausted. Remaining uploads will likely fail too.");
    }
    // Continue to next video instead of crashing the batch
  }
}

console.log(`\n${uploaded}/${videos.length} videos uploaded successfully${failed ? ` (${failed} failed)` : ""}. Scheduled at peak IST times (8AM/1PM/6PM).`);
