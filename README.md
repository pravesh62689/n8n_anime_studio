# Anime Kids Studio 4.0 — Free Viral Video Generator

Generates **fully animated, Cocomelon-style Hinglish kids' videos** for YouTube using 100% free resources. No credits, no API keys, no limits.

## What changed vs. the old pipeline

| Old (boring) | New (engaging) |
|---|---|
| ffmpeg zoompan on static images | Real 2D animation: bouncing, dancing, squash-and-stretch characters (Remotion) |
| No music | Synthesized upbeat kids' music bed (pure Node, no downloads, no copyright strikes) |
| Plain narration | Hinglish sing-along rhymes + karaoke-style highlighted lyrics |
| Static text | Animated word-pop lyrics, confetti, stars, floating particles |

## Free stack

- **Remotion** — programmatic animation engine (free for individuals/small teams), renders on CPU — works on your 8-12GB laptop
- **Pollinations AI** — free unlimited image generation (characters, backgrounds)
- **Microsoft Edge TTS** (`msedge-tts`) — free natural Hindi neural voice (SwaraNeural)
- **Node music synth** — royalty-free upbeat music generated in code

## Usage

```bash
npm install

# 1. Generate all assets (images, TTS voice, music, timing data)
npm run generate

# 2. Preview in browser (Remotion Studio)
npm run dev

# 3. Render final videos (1080p MP4, YouTube-ready)
npm run render        # Rhyme/song video
npm run render-story  # Story video
```

Output lands in `out/`.

## Making new videos

Edit `pipeline/content.mjs` — change the rhyme lines, story scenes, and image prompts, then re-run `npm run generate` + `npm run render`. Each line automatically gets:
- its own AI-generated illustration
- TTS audio with measured duration (perfect sync)
- karaoke lyric highlighting and character choreography

## Channel growth playbook (10K subs target)

1. **Consistency**: upload 3+ videos/week — the pipeline makes each video in ~15 min
2. **Titles**: Hinglish keyword-rich, e.g. "Hathi Raja Kahan Chale | Hindi Rhymes for Kids | Nursery Song"
3. **Thumbnails**: use the generated character images — big faces, bright colors, minimal text
4. **Shorts**: render 9:16 cuts of the catchiest 30s of each rhyme (add a Short composition in `src/Root.tsx`)
5. **Playlists + end screens**: chain rhymes so autoplay keeps kids watching

## Project layout

```
pipeline/content.mjs    <- EDIT THIS to make new videos (lyrics, scenes, prompts)
pipeline/generate.mjs   <- fetches images, synthesizes TTS + music, writes timing
pipeline/music.mjs      <- royalty-free kids' music synthesizer
src/Root.tsx            <- Remotion compositions (RhymeVideo, StoryVideo)
src/RhymeVideo.tsx      <- sing-along rhyme with karaoke + dancing characters
src/StoryVideo.tsx      <- animated story with parallax scenes
src/components/         <- Character, Karaoke, Particles, SceneBg animators
public/assets/          <- generated images, audio, music
src/data/timeline.json  <- generated timing data (audio-synced)
```

## Legacy Python pipeline

The previous zoompan-based Python pipeline (`orchestrator.py`, `studio_core.py`, `render_masterpiece.py`, `studio_mcp.py`) is kept for reference but is superseded by the Remotion engine above.
