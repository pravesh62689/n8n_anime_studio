import os
import wave
import subprocess
import numpy as np
from pathlib import Path
from studio_core import get_ffmpeg_paths

SAMPLE_RATE = 44100

def save_wav(data, path: Path):
    data = np.clip(data, -1.0, 1.0)
    data_int = (data * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(data_int.tobytes())

def convert_to_mp3(wav_path: Path, mp3_path: Path):
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    cmd = [
        ffmpeg_cmd, "-y",
        "-i", str(wav_path),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(mp3_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if wav_path.exists():
        wav_path.unlink()

# --- Instruments Synths ---

def marimba_note(freq, duration, volume=0.5):
    """Marimba-like note using short attack, exponential decay, and weak odd harmonics."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Harmonics
    wave_data = np.sin(2 * np.pi * freq * t)
    wave_data += 0.4 * np.sin(2 * np.pi * 3 * freq * t)
    wave_data += 0.2 * np.sin(2 * np.pi * 5 * freq * t)
    
    # Attack-Decay envelope
    decay = np.exp(-7.0 * t)
    attack = np.minimum(t / 0.005, 1.0)
    env = attack * decay
    return wave_data * env * volume

def piano_note(freq, duration, volume=0.5):
    """Piano-like note using decay and a few integer harmonics."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave_data = np.sin(2 * np.pi * freq * t)
    wave_data += 0.3 * np.sin(2 * np.pi * 2 * freq * t)
    wave_data += 0.1 * np.sin(2 * np.pi * 3 * freq * t)
    
    decay = np.exp(-2.0 * t)
    attack = np.minimum(t / 0.02, 1.0)
    env = attack * decay
    return wave_data * env * volume

def pluck_note(freq, duration, volume=0.5):
    """Karplus-Strong pluck synthesis for rich guitar/plucked-string vibe."""
    N = int(SAMPLE_RATE / freq)
    if N <= 1:
        return np.zeros(int(SAMPLE_RATE * duration))
    # Ring buffer initialized with white noise
    buf = np.random.uniform(-1.0, 1.0, N)
    out = np.zeros(int(SAMPLE_RATE * duration))
    for i in range(len(out)):
        out[i] = buf[0]
        # Lowpass filter/decay feedback loop
        val = 0.996 * 0.5 * (buf[0] + buf[1])
        buf = np.append(buf[1:], val)
    
    # Fadeout to avoid clicks at the end
    t = np.linspace(0, duration, len(out))
    fade = np.minimum(1.0, (duration - t) / 0.1)
    return out * fade * volume

def orchestral_chord(frequencies, duration, volume=0.4):
    """Synthesizes a rich orchestral swell chord."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    data = np.zeros_like(t)
    for freq in frequencies:
        # fundamental + warm octaves + fifths
        data += np.sin(2 * np.pi * freq * t)
        data += 0.4 * np.sin(2 * np.pi * (freq * 2) * t)
        data += 0.25 * np.sin(2 * np.pi * (freq * 1.5) * t)
    data /= len(frequencies)
    
    # Swell envelope (slow attack, long release)
    attack_len = int(SAMPLE_RATE * duration * 0.4)
    decay_len = len(t) - attack_len
    attack = np.linspace(0.0, 1.0, attack_len)
    decay = np.linspace(1.0, 0.0, decay_len)
    env = np.concatenate([attack, decay])
    return data * env * volume

# --- Background Music Beds (BGM) ---

def generate_bgm_1(duration):
    """BGM 1: Upbeat, fast-paced marimba/ukulele loop."""
    # Play major pentatonic arpeggios
    notes = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25] # C4, D4, E4, G4, A4, C5
    tempo = 0.15 # seconds per note
    n_notes = int(duration / tempo) + 1
    data = []
    for i in range(n_notes):
        freq = notes[i % len(notes)]
        # alternate marimba and pluck
        if i % 2 == 0:
            note_data = marimba_note(freq, tempo, volume=0.35)
        else:
            note_data = pluck_note(freq, tempo, volume=0.3)
        data.append(note_data)
    combined = np.concatenate(data)[:int(SAMPLE_RATE * duration)]
    return combined

def generate_bgm_2(duration):
    """BGM 2: Curious, sneaky music plucks."""
    notes = [220.00, 261.63, 293.66, 311.13, 293.66, 261.63] # A3, C4, D4, Eb4, D4, C4
    tempo = 0.35
    n_notes = int(duration / tempo) + 1
    data = []
    for i in range(n_notes):
        freq = notes[i % len(notes)]
        note_data = pluck_note(freq, tempo, volume=0.4)
        data.append(note_data)
    combined = np.concatenate(data)[:int(SAMPLE_RATE * duration)]
    return combined

def generate_bgm_3(duration):
    """BGM 3: Slightly tense and mischievous minor seconds."""
    notes = [146.83, 155.56, 146.83, 155.56] # D3, Eb3 (Tension)
    tempo = 0.4
    n_notes = int(duration / tempo) + 1
    data = []
    for i in range(n_notes):
        freq = notes[i % len(notes)]
        note_data = marimba_note(freq, tempo, volume=0.45)
        data.append(note_data)
    combined = np.concatenate(data)[:int(SAMPLE_RATE * duration)]
    return combined

def generate_bgm_4(duration):
    """BGM 4: Slow, sad piano chords."""
    # Chords: Am (110, 130.81, 164.81), Dm (146.83, 174.61, 220.00)
    chords = [
        [220.00, 261.63, 329.63], # Am
        [293.66, 349.23, 440.00], # Dm
        [174.61, 220.00, 261.63], # F
        [196.00, 246.94, 293.66], # G
    ]
    chord_duration = 2.0
    n_chords = int(duration / chord_duration) + 1
    data = []
    for i in range(n_chords):
        chosen = chords[i % len(chords)]
        chord_data = np.zeros(int(SAMPLE_RATE * chord_duration))
        for freq in chosen:
            chord_data += piano_note(freq, chord_duration, volume=0.3)
        data.append(chord_data / len(chosen))
    combined = np.concatenate(data)[:int(SAMPLE_RATE * duration)]
    return combined

def generate_bgm_5(duration):
    """BGM 5: Happy, triumphant major-scale plucks."""
    notes = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63] # C4, E4, G4, C5, G4, E4
    tempo = 0.25
    n_notes = int(duration / tempo) + 1
    data = []
    for i in range(n_notes):
        freq = notes[i % len(notes)]
        note_data = pluck_note(freq, tempo, volume=0.35)
        data.append(note_data)
    combined = np.concatenate(data)[:int(SAMPLE_RATE * duration)]
    return combined

def generate_bgm_6(duration):
    """BGM 6: Full orchestral happy swell chord."""
    # Grand C major swell
    chord_freqs = [130.81, 196.00, 261.63, 329.63, 392.00, 523.25]
    return orchestral_chord(chord_freqs, duration, volume=0.45)

# --- Sound Effects Synths (SFX) ---

def generate_sfx_rustle_giggle(duration):
    """SFX 1: Leaf rustles (filtered noise) followed by cute giggling chirps."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # 1. Rustle (White noise modulated by low frequency wind-like wave)
    noise = np.random.normal(0.0, 0.25, len(t))
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * 3.0 * t) # 3Hz modulation
    rustle = noise * mod
    
    # Lowpass filter the rustle slightly
    rustle = np.convolve(rustle, np.ones(5)/5.0, mode='same')
    
    # 2. Giggle chirps (high pitched frequency-swept sine waves near the end)
    giggle = np.zeros_like(t)
    start_idx = int(SAMPLE_RATE * (duration - 1.5))
    if start_idx > 0:
        t_giggle = t[start_idx:]
        # Generate 4 quick giggles
        for pulse in range(4):
            pulse_start = 0.3 * pulse
            p_t = t_giggle - t_giggle[0] - pulse_start
            p_mask = (p_t >= 0) & (p_t < 0.15)
            # Sweeping sine frequency: 800Hz to 1200Hz
            freq_sweep = 800 + 1500 * (p_t[p_mask] / 0.15)
            giggle[start_idx:][p_mask] = 0.25 * np.sin(2 * np.pi * freq_sweep * p_t[p_mask]) * np.exp(-15.0 * p_t[p_mask])
            
    combined = rustle * 0.4 + giggle * 0.6
    return combined

def generate_sfx_sparkle(duration):
    """SFX 2: Sparkling chime sound (*ting*)."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    sparkle = np.zeros_like(t)
    # Generate multiple overlapping high-pitched bell tones
    bell_freqs = [1800.0, 2200.0, 2700.0, 3200.0]
    for idx, freq in enumerate(bell_freqs):
        delay = 0.05 * idx
        t_delay = t - delay
        mask = t_delay >= 0
        sparkle[mask] += 0.2 * np.sin(2 * np.pi * freq * t_delay[mask]) * np.exp(-8.0 * t_delay[mask])
    return sparkle

def generate_sfx_chatter_whoosh(duration):
    """SFX 3: Mischievous monkey chatter (chirps) + quick whoosh sweep."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Chatter (high pitched chirp pulses)
    chatter = np.zeros_like(t)
    for p in range(6):
        pulse_start = 0.2 * p
        p_t = t - pulse_start
        mask = (p_t >= 0) & (p_t < 0.12)
        # Sweeping frequency
        freq = 1200 + 800 * np.sin(2 * np.pi * 15 * p_t[mask])
        chatter[mask] += 0.2 * np.sin(2 * np.pi * freq * p_t[mask]) * np.exp(-12.0 * p_t[mask])
        
    # Whoosh (noise frequency sweep)
    whoosh = np.zeros_like(t)
    whoosh_start = duration - 1.0
    p_t = t - whoosh_start
    mask = (p_t >= 0) & (p_t < 0.8)
    if np.any(mask):
        noise = np.random.normal(0, 0.3, np.sum(mask))
        # sweep filter coefficients dynamically or simulate with modulated noise envelope
        env = np.sin(np.pi * p_t[mask] / 0.8)
        whoosh[mask] = noise * env * 0.5
        whoosh = np.convolve(whoosh, np.ones(8)/8.0, mode='same')
        
    return chatter * 0.5 + whoosh * 0.5

def generate_sfx_wind_sigh(duration):
    """SFX 4: Melancholic wind blowing and soft sigh."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Wind (low pass noise with sinusoidal frequency modulation)
    noise = np.random.normal(0, 0.25, len(t))
    mod = 0.6 + 0.3 * np.sin(2 * np.pi * 0.2 * t) # very slow wind sway
    wind = noise * mod
    wind = np.convolve(wind, np.ones(12)/12.0, mode='same') # low pass
    
    # Sad sigh (low pitch breathing hum near the end)
    sigh = np.zeros_like(t)
    sigh_start = duration - 2.0
    p_t = t - sigh_start
    mask = (p_t >= 0) & (p_t < 1.2)
    if np.any(mask):
        # 150Hz soft hum
        env = np.sin(np.pi * p_t[mask] / 1.2)
        sigh[mask] = 0.15 * np.sin(2 * np.pi * 150.0 * p_t[mask]) * env
        
    return wind * 0.6 + sigh * 0.4

def generate_sfx_footsteps(duration):
    """SFX 5: Running footsteps (regular low-frequency thuds)."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    steps = np.zeros_like(t)
    step_interval = 0.35 # seconds
    n_steps = int(duration / step_interval)
    for s in range(n_steps):
        delay = step_interval * s
        p_t = t - delay
        mask = (p_t >= 0) & (p_t < 0.15)
        # Low frequency thump (80Hz decaying) + friction high frequency noise
        thump = 0.4 * np.sin(2 * np.pi * 80.0 * p_t[mask]) * np.exp(-20.0 * p_t[mask])
        friction = 0.15 * np.random.normal(0, 0.1, np.sum(mask)) * np.exp(-35.0 * p_t[mask])
        steps[mask] += thump + friction
    return steps

def generate_sfx_magical_cheers(duration):
    """SFX 6: Massive magical burst followed by children cheering."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Magical burst at start
    burst = np.zeros_like(t)
    # sweep multiple frequency waves from low to high
    burst_mask = t < 1.0
    for f_start in [100.0, 200.0, 300.0]:
        freq = f_start + 1800.0 * t[burst_mask]
        burst[burst_mask] += 0.15 * np.sin(2 * np.pi * freq * t[burst_mask])
    burst[burst_mask] *= np.exp(-3.0 * t[burst_mask])
    
    # Cheering (white noise bandpass filtered with amplitude modulation resembling cheering)
    cheers = np.zeros_like(t)
    cheer_start = 0.5
    p_t = t - cheer_start
    mask = p_t >= 0
    if np.any(mask):
        noise = np.random.normal(0, 0.2, np.sum(mask))
        # cheer frequency peaks filter simulated with convolution
        env = (1.0 - np.exp(-2.0 * p_t[mask])) * np.exp(-0.25 * p_t[mask]) # rise and decay
        cheers[mask] = noise * env * 0.6
        # smooth
        cheers = np.convolve(cheers, np.ones(6)/6.0, mode='same')
        
    return burst * 0.5 + cheers * 0.5

# --- Main Synthesis Coordinator ---

def main():
    print("[Synthesizer] Initiating Sound Design Asset Generation...")
    assets_dir = Path.cwd() / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    # Track configurations: (filename_prefix, bgm_func, sfx_func, duration)
    # Match durations roughly to script timeline scenes
    scenes_sound_cfg = [
        ("scene_1", generate_bgm_1, generate_sfx_rustle_giggle, 8.0),
        ("scene_2", generate_bgm_2, generate_sfx_sparkle, 8.0),
        ("scene_3", generate_bgm_3, generate_sfx_chatter_whoosh, 9.0),
        ("scene_4", generate_bgm_4, generate_sfx_wind_sigh, 9.0),
        ("scene_5", generate_bgm_5, generate_sfx_footsteps, 8.0),
        ("scene_6", generate_bgm_6, generate_sfx_magical_cheers, 8.0),
    ]
    
    for prefix, bgm_fn, sfx_fn, dur in scenes_sound_cfg:
        print(f"[Synthesizer] Synthesizing audio beds for {prefix} (duration: {dur}s)...")
        bgm_data = bgm_fn(dur)
        sfx_data = sfx_fn(dur)
        
        # Save temp WAV files
        bgm_wav = assets_dir / f"bgm_{prefix}.wav"
        sfx_wav = assets_dir / f"sfx_{prefix}.wav"
        
        save_wav(bgm_data, bgm_wav)
        save_wav(sfx_data, sfx_wav)
        
        # Convert to MP3
        bgm_mp3 = assets_dir / f"bgm_{prefix}.mp3"
        sfx_mp3 = assets_dir / f"sfx_{prefix}.mp3"
        
        convert_to_mp3(bgm_wav, bgm_mp3)
        convert_to_mp3(sfx_wav, sfx_mp3)
        
        print(f"[Synthesizer] [OK] Generated: bgm_{prefix}.mp3 and sfx_{prefix}.mp3")
        
    print("[Synthesizer] Sound design audio compilation complete!")

if __name__ == "__main__":
    main()
