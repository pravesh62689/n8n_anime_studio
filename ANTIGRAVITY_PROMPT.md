# Implementation Directive for Antigravity — Anime Studio: 3-Tier Visual Pipeline

Paste this whole thing in. It references the actual files you've already shown me you can see (`studio_core.py`, `generate_anime_video()`, `orchestrator.py`, the `*_mcp.py` files, `n8n_workflow_template.json`) — don't rebuild from scratch, wire this into what's already there.

## The problem you need to fix, stated precisely

`generate_anime_video()` currently has two paths: real Wan2.1 motion (via HF Gradio Space, with last-frame chaining), and a zoompan/parallax fallback when Wan2.1 fails or queues out. That's the right idea, but the math doesn't work: free HF ZeroGPU quota is roughly 2-4 successful generations per day, and a 30-scene video needs ~30 real clips. **That means 85-95% of scenes are structurally guaranteed to hit the fallback, regardless of whether the Wan2.1 integration works correctly.** This is why the rendered output is mostly still images with a pan, even though the code has a real-motion path. Do not "fix" this by trying to make Wan2.1 succeed more often — the ceiling is the daily quota, not the code.

## What to build instead: a third tier

Insert a new tier between the existing two:

1. **Tier 1 (existing, keep as-is)** — real Wan2.1 motion via HF Space, last-frame chained for consistency. Reserve this for **1-3 explicitly-flagged hero beats per video** (the emotional peak, the climax) — not every scene. Gate every call behind a local quota tracker (see below) that refuses the attempt if today's estimated budget is already spent, rather than discovering the failure via a 429 mid-render.

2. **Tier 2 (new — build this)** — pose-sequence hard-cut animation. For every scene that isn't a Tier-1 hero beat and isn't a genuinely static shot, generate 3-6 sequential pose stills of the same locked character performing the action (anticipation → peak action → impact → follow-through), using Pollinations' free unlimited Flux endpoint with a fixed seed, a locked style-suffix string, and the character's reference image passed as conditioning on every single call. Hard-cut the stills together with ffmpeg (front-load the hold duration on the anticipation/impact poses, shorter holds on follow-through). This is free, unlimited, and does not touch HF quota at all. **This becomes the default for most scenes — not the exception.**

3. **Tier 3 (rename the existing fallback)** — multi-layer parallax zoompan. Reserve this only for shots that are narratively static (an establishing shot, a quiet dialogue beat where nothing needs to visibly happen) — not as the default catch-all it currently is.

## Required: a local quota tracker, checked BEFORE attempting Tier 1

Add a small persistent tracker (`quota.py` — plain JSON file, `{date, seconds_used}`, resets ~24h after first use) that the Visual Router consults before calling Wan2.1. `HF_DAILY_QUOTA_SECONDS` ≈ 190 (leave margin under the real ~210s/day ceiling for a logged-in free account), `HF_ESTIMATED_COST_PER_CLIP_SECONDS` — read the actual "X requested vs Y left" numbers HF returns on a real call and set this to match, don't guess. `can_afford()` gates the attempt; `record_usage()` updates it after every real call, success or failure (failed calls still spend GPU time).

## Required: report actual tier usage, not capability

After every render, output a manifest — not a prose summary — showing, per scene: which tier actually ran, and if Tier 1 was attempted and fell back, why (quota exhausted / Space error / timeout). Example:

```json
{
  "video_id": "test_001",
  "scenes": [
    {"scene": 1, "tier_attempted": 1, "tier_used": 1, "fallback_reason": null},
    {"scene": 2, "tier_attempted": 2, "tier_used": 2, "fallback_reason": null},
    {"scene": 3, "tier_attempted": 1, "tier_used": 2, "fallback_reason": "quota_exhausted"}
  ],
  "tier_1_count": 1, "tier_2_count": 2, "tier_3_count": 0
}
```

Do not report this project as "using Wan2.1 for true video motion" again unless this manifest shows it on the majority of scenes it was attempted for. If the honest number is "3 out of 30 scenes got Tier 1," say that number, not the capability.

## Acceptance criteria (concrete, checkable — not "make it look like real anime")

- Zero scenes in the final output are a single static image with only a camera pan, except scenes explicitly marked as establishing/static shots in the script.
- Every action/dialogue scene is either Tier 1 or Tier 2.
- The character's face, outfit, and palette are recognizably the same across every pose in a Tier-2 sequence (same locked seed + style suffix + reference image on every generation call in that sequence).
- The end-of-render manifest above is produced and attached to the delivery — not just a description of what the code should do.

## Start smaller than 30 scenes

Test this on an 8-10 scene, ~60-90 second cut first. At that scene count, the existing Tier-1 quota can meaningfully cover 2-4 of them for real, so you can verify the whole 3-tier system actually behaves as designed before scaling back up to the full 4-5 minute format.

## Do not attempt

- Do not try to get more Tier-1 volume by calling multiple duplicate/forked HF Spaces under the same account or token — quota is tracked per-account, not per-Space; this spreads queue congestion, it does not add capacity.
- Do not raise output frame rate above 30fps (60 only for the zoompan-tier camera pans specifically, if wanted) — it does not fix motion quality and roughly doubles encode time on this hardware for no visible benefit.
- Do not present a code-capability description as if it were a report of what a specific render actually produced.
