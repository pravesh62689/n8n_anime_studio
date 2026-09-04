# Anime Studio — Next Steps README (Kids Storytelling Focus)

## 1. What the reference kit is actually for

You already have `studio_core.py`, `render_masterpiece.py`, `*_mcp.py`, and an n8n workflow template. The reference kit is **not** a replacement — it's the four pieces your rebuild blueprint (§2, §4) called for that don't exist yet in your repo:

| File | Purpose |
|---|---|
| `quota.py` | Tracks your free HF ZeroGPU video budget (~190s/day) so Tier-1 calls get gated *before* they fail, not after |
| `pose_sequence.py` | The new Tier-2 method: 3–6 locked-character pose stills, hard-cut with ffmpeg — free, unlimited, no HF quota used |
| `db.py` | The RAG/analytics database — where retention scores eventually get written and read back for script generation |
| `ANTIGRAVITY_PROMPT.md` | Paste this into an AI coding tool (Antigravity or similar) pointed at your real source files — it's the implementation spec, not code to run standalone |
| `.env.example` / `requirements.txt` | Config and dependency list matching the above |

**Action:** copy these into your existing repo, then either hand `ANTIGRAVITY_PROMPT.md` to your coding tool to wire them into `studio_core.py`, or paste your real source here and I'll patch it directly.

---

## 2. Storytelling for kids — what actually works (researched, not assumed)

- Younger viewers respond better to **fast pacing, frequent visual changes, and simple, direct storytelling** than adults do.
- **First 10–15 seconds decide retention** — open on your most visually interesting beat, not a slow intro.
- **Storytelling with recognizable characters** builds emotional engagement and identification — this is *why* format beats raw content volume.
- Current winning shape: **Shorts for discovery, longer episodes for binge/retention** — most fast-growing kids channels hit their first 100K subs through Shorts, then convert into full-episode watchers.
- Hot kids sub-niches right now: nursery rhymes, phonics, sensory animation, emotional learning, simple STEM — worth considering even alongside an action/adventure format.

### Honest translation to your pipeline
One Piece/Black Clover-level animation needs a studio's frame budget — your free-tier stack can't do that, and won't. What it *can* do well:
- Recognizable, consistent characters (locked seed + style suffix + reference image every call)
- Clear physical beats: anticipation → peak action → impact → follow-through (exactly what `pose_sequence.py` generates)
- One real-motion hero beat per episode (Tier 1), everything else Tier 2/3

### Concrete steps
1. Lock a style bible — one reference image + fixed style string + seed per character, before writing any scripts.
2. Write scripts in 3–6 beat sequences per scene, matching what Tier 2 can actually produce.
3. Open every episode on its strongest visual beat.
4. Start at 60–90 seconds (Phase 1), not 4–5 minutes — get the pipeline finishing reliably first.
5. One Tier-1 hero beat per episode (the emotional climax), rest Tier 2/3.
6. Don't let your own analytics bias script generation until 10–15 published episodes exist — before that, the data is noise (see blueprint §8).

---

## 3. Free, no-code n8n automation — what's real right now

| Need | Template / Tool | Notes |
|---|---|---|
| YouTube upload + scheduling | [n8n YouTube integration](https://n8n.io/integrations/youtube/) + [scheduling & AI metadata template](https://n8n.io/workflows/3900-automated-youtube-video-scheduling-and-ai-metadata-generation/) | Native node, free on self-hosted n8n. Upload private → publish on schedule. |
| Multi-platform (Instagram, TikTok, YouTube, FB, LinkedIn) | [Upload-Post n8n templates](https://www.upload-post.com/n8n-templates/) | Free to import; Upload-Post free tier = 10 uploads/month |
| Long video → Shorts repurposing | [GitHub: N8N-Youtube-Workflow](https://github.com/tomash-dev/N8N-Youtube-Workflow) | Needs a clip-rendering service (e.g. Swiftia) — check its free tier before committing |
| General automation (Sheets, Drive, Discord alerts, AI) | [awesome-n8n-templates (280+ free)](https://github.com/enescingoz/awesome-n8n-templates) | Largest open collection, includes AI/RAG and social templates |
| Queue-and-trigger pattern | Google Sheet with a `status` column → n8n watches it → Execute Command node runs your local Python | Matches your own blueprint §10 exactly |

**Not solved by n8n:** the 3D-animated/expert-UI website. That's a real build (React + Tailwind, or Three.js for 3D elements), not a workflow template. Tell me what the site needs to do — channel landing page, episode archive, merch page later — and I'll build it directly rather than point you at templates that won't fit.

---

## 4. Suggested order of operations

1. Drop the reference kit files into your repo; apply `ANTIGRAVITY_PROMPT.md` via your coding tool.
2. Lock character style bible.
3. Produce one 60–90s test episode using the honest Tier 1/2/3 mix above.
4. Wire the n8n Google-Sheet-queue → YouTube-upload pattern once the mechanical pipeline is reliable.
5. Add Instagram/multi-platform via Upload-Post once YouTube alone is working end-to-end.
6. Revisit the website and Shorts-repurposing automation as separate, later phases — don't stack all of this at once (same "boring and reliable before scaling" principle as your blueprint's Phase 4).
