// One-time YouTube OAuth setup. Run: node pipeline/youtube-auth.mjs
// Prerequisite (free, ~5 min):
//   1. Go to https://console.cloud.google.com -> create a project
//   2. Enable "YouTube Data API v3"
//   3. Create OAuth credentials (Desktop app) -> get CLIENT_ID + CLIENT_SECRET
//   4. Set env vars YT_CLIENT_ID and YT_CLIENT_SECRET, then run this script.
// It prints an auth URL — open it, approve, paste the code back. Saves a refresh
// token to .yt-token.json (gitignored) which the uploader uses forever after.

import { google } from "googleapis";
import { writeFileSync } from "node:fs";
import { createInterface } from "node:readline/promises";

const { YT_CLIENT_ID, YT_CLIENT_SECRET } = process.env;
if (!YT_CLIENT_ID || !YT_CLIENT_SECRET) {
  console.error("Set YT_CLIENT_ID and YT_CLIENT_SECRET env vars first (see comments at top of this file).");
  process.exit(1);
}

const oauth2 = new google.auth.OAuth2(YT_CLIENT_ID, YT_CLIENT_SECRET, "urn:ietf:wg:oauth:2.0:oob");
const url = oauth2.generateAuthUrl({
  access_type: "offline",
  scope: ["https://www.googleapis.com/auth/youtube.upload"],
  prompt: "consent",
});

console.log("\n1. Open this URL in your browser and approve:\n\n" + url + "\n");
const rl = createInterface({ input: process.stdin, output: process.stdout });
const code = await rl.question("2. Paste the code here: ");
rl.close();

const { tokens } = await oauth2.getToken(code.trim());
writeFileSync(".yt-token.json", JSON.stringify(tokens, null, 2));
console.log("\nDone! Refresh token saved to .yt-token.json. You can now run: npm run upload");
