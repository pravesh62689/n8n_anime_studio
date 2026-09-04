// Synthesizes a royalty-free, bouncy kids music loop as a WAV file. 100% free, no API.
import fs from "node:fs";

const SR = 44100;
const BPM = 118;
const beat = 60 / BPM;

const note = (n) => 440 * Math.pow(2, (n - 69) / 12); // midi -> hz

// C major bounce: I - V - vi - IV, one chord per bar (4 beats), 8 bars
const CHORDS = [
  [60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60],
  [60, 64, 67], [55, 59, 62], [57, 60, 64], [55, 59, 62],
];
// Plucky melody (midi, start-beat, len-beats) over 8 bars
const MELODY = [
  [72,0,.5],[76,.5,.5],[79,1,1],[76,2,.5],[72,2.5,.5],[74,3,1],
  [71,4,.5],[74,4.5,.5],[79,5,1],[74,6,.5],[71,6.5,.5],[72,7,1],
  [69,8,.5],[72,8.5,.5],[76,9,1],[72,10,.5],[69,10.5,.5],[71,11,1],
  [65,12,.5],[69,12.5,.5],[72,13,1],[74,14,.5],[76,14.5,.5],[77,15,1],
  [79,16,.5],[76,16.5,.5],[72,17,1],[76,18,.5],[79,18.5,.5],[81,19,1],
  [79,20,.5],[74,20.5,.5],[71,21,1],[74,22,1],[79,23,1],
  [76,24,.5],[72,24.5,.5],[69,25,1],[72,26,.5],[76,26.5,.5],[74,27,1],
  [72,28,.5],[74,28.5,.5],[76,29,.5],[77,29.5,.5],[79,30,2],
];

export function makeMusic(outPath) {
  const totalBeats = 32;
  const len = Math.floor(totalBeats * beat * SR);
  const buf = new Float32Array(len);

  const add = (freq, start, dur, vol, type = "tri") => {
    const s0 = Math.floor(start * SR);
    const n = Math.floor(dur * SR);
    for (let i = 0; i < n && s0 + i < len; i++) {
      const t = i / SR;
      const env = Math.min(1, i / 300) * Math.exp(-2.5 * (t / dur));
      const ph = 2 * Math.PI * freq * t;
      let v;
      if (type === "tri") v = (2 / Math.PI) * Math.asin(Math.sin(ph));
      else if (type === "sine") v = Math.sin(ph);
      else v = Math.sin(ph) * 0.6 + Math.sin(2 * ph) * 0.3; // warm
      buf[s0 + i] += v * env * vol;
    }
  };

  for (let bar = 0; bar < 8; bar++) {
    const chord = CHORDS[bar];
    for (let b = 0; b < 4; b++) {
      const t = (bar * 4 + b) * beat;
      // bass thump on every beat
      add(note(chord[0] - 24), t, beat * 0.5, 0.22, "sine");
      // off-beat chord stabs (ukulele-ish bounce)
      chord.forEach((m) => add(note(m), t + beat * 0.5, beat * 0.35, 0.06, "warm"));
      // soft kick
      const s0 = Math.floor(t * SR);
      for (let i = 0; i < 2200 && s0 + i < len; i++) {
        const tt = i / SR;
        buf[s0 + i] += Math.sin(2 * Math.PI * (110 - 700 * tt) * tt) * Math.exp(-30 * tt) * 0.3;
      }
    }
  }
  for (const [m, st, d] of MELODY) add(note(m), st * beat, d * beat * 0.95, 0.14, "tri");

  // normalize + write 16-bit WAV
  let peak = 0;
  for (const v of buf) peak = Math.max(peak, Math.abs(v));
  const wav = Buffer.alloc(44 + len * 2);
  wav.write("RIFF", 0); wav.writeUInt32LE(36 + len * 2, 4); wav.write("WAVEfmt ", 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(SR, 24); wav.writeUInt32LE(SR * 2, 28); wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34); wav.write("data", 36); wav.writeUInt32LE(len * 2, 40);
  for (let i = 0; i < len; i++) wav.writeInt16LE(Math.round((buf[i] / peak) * 0.85 * 32767), 44 + i * 2);
  fs.writeFileSync(outPath, wav);
}
