"""A small synthesizer for the game's soundtracks: instruments, effects and a mixer, in numpy and scipy.

Every instrument returns the audio of one note (mono, or stereo as an (n, 2) array). A Song collects notes per
stem; mix() balances the stems, adds reverb and delay, and folds the tail back onto the start so the track loops
without a gap. master() sets the loudness and keeps the peaks under -1 dBFS.
"""

import numpy as np
from scipy import signal

SR = 44100
_rng = np.random.default_rng(20260930)
TAU = 2 * np.pi


def reseed(seed):
    global _rng
    _rng = np.random.default_rng(seed)


def rng():
    return _rng


# ----------------------------------------------------------------- notes ---

_LETTERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(note):
    """'C#4', 'Bb3', 'F#5' -> MIDI number (A4 = 69). Numbers pass through."""
    if not isinstance(note, str):
        return int(note)
    i, acc = 1, 0
    while note[i] in "#b":
        acc += 1 if note[i] == "#" else -1
        i += 1
    return 12 * (int(note[i:]) + 1) + _LETTERS[note[0]] + acc


def hz(note):
    return 440.0 * 2 ** ((midi(note) - 69) / 12)


# --------------------------------------------------------------- filters ---

_sos_cache = {}


def _sos(kind, fc, order):
    key = (kind, fc, order)
    if key not in _sos_cache:
        _sos_cache[key] = signal.butter(order, fc, kind, fs=SR, output="sos")
    return _sos_cache[key]


def lowpass(x, fc, order=2):
    return signal.sosfilt(_sos("lowpass", round(min(fc, SR * 0.45), 1), order), x, axis=0)


def highpass(x, fc, order=2):
    return signal.sosfilt(_sos("highpass", round(fc, 1), order), x, axis=0)


def bandpass(x, lo, hi, order=2):
    lo, hi = max(lo, 20.0), min(hi, SR * 0.45)
    return signal.sosfilt(_sos("bandpass", (round(lo, 1), round(hi, 1)), order), x, axis=0)


# ------------------------------------------------------------- envelopes ---

def adsr(hold, a, d, s, r):
    """Envelope for a note held `hold` seconds: attack a, decay d (to level s), then release r after the hold."""
    nh, nr = max(1, int(hold * SR)), max(1, int(r * SR))
    t = np.arange(nh) / SR
    att = np.sin(np.clip(t / max(a, 1e-4), 0, 1) * np.pi / 2)
    dec = s + (1 - s) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    e = np.empty(nh + nr)
    e[:nh] = np.where(t < a, att, dec)
    tr = np.arange(nr) / SR
    e[nh:] = e[nh - 1] * np.exp(-tr / (r / 4.5)) * (1 - tr / r)
    return e


def fade(n, fade_in, fade_out):
    e = np.ones(n)
    i, o = min(n, int(fade_in * SR)), min(n, int(fade_out * SR))
    if i:
        e[:i] = np.sin(np.linspace(0, np.pi / 2, i)) ** 2
    if o:
        e[n - o:] *= np.cos(np.linspace(0, np.pi / 2, o)) ** 2
    return e


# ----------------------------------------------------------- oscillators ---

def _freqs(freq, n):
    return np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq, float)


def phase(freq, n, start=None):
    f = _freqs(freq, n)
    p0 = _rng.random() if start is None else start
    return (p0 + np.cumsum(f) / SR) % 1.0, f / SR


def sine(freq, n, start=None):
    return np.sin(TAU * phase(freq, n, start)[0])


def saw(freq, n, start=None):
    """Band-limited sawtooth (polyBLEP), so high notes don't alias."""
    ph, dt = phase(freq, n, start)
    y = 2 * ph - 1
    m = ph < dt
    t = ph[m] / dt[m]
    y[m] -= t + t - t * t - 1
    m = ph > 1 - dt
    t = (ph[m] - 1) / dt[m]
    y[m] -= t * t + t + t + 1
    return y


def vibrato(f0, n, rate=5.2, depth=0.004, delay=0.2, ramp=0.3):
    t = np.arange(n) / SR
    amount = depth * np.clip((t - delay) / ramp, 0, 1)
    return f0 * (1 + amount * np.sin(TAU * rate * t + _rng.random() * TAU))


def noise(n):
    return _rng.standard_normal(n)


def pan2(x, pan):
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


# ------------------------------------------------------------ instruments ---

def flute(note, dur, vel=1.0, breath=0.05, vib=0.0045):
    """Breathy wooden flute: soft harmonics, a little chiff at the start and a vibrato that grows in."""
    f0 = hz(note)
    env = adsr(dur, 0.05, 0.25, 0.85, 0.14)
    n = len(env)
    t = np.arange(n) / SR
    ph = TAU * np.cumsum(vibrato(f0, n, rate=5.3, depth=vib, delay=0.18, ramp=0.35)) / SR
    tone = np.sin(ph) + 0.26 * np.sin(2 * ph + 0.4) + 0.08 * np.sin(3 * ph + 1.1) + 0.03 * np.sin(4 * ph + 2.0)
    air = bandpass(noise(n), 1500, 7500)
    y = 0.9 * tone + air * (breath + 0.22 * np.exp(-t / 0.025))
    swell = 1 + 0.1 * np.clip(t / max(dur, 0.2), 0, 1)
    return y * env * swell * vel


def pluck(note, vel=1.0, decay=2.0, pos=0.2, bright=0.5, length=None, damp=None):
    """Plucked string (harp, pizzicato) from decaying harmonics: higher harmonics die away faster."""
    f0 = hz(note)
    length = length or min(6.0, decay * 3.5)
    n = int(length * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    total = 0.0
    for k in range(1, int(min(32, 14000 / f0)) + 1):
        a = abs(np.sin(np.pi * k * pos)) / k ** (2.0 - bright)
        if a < 1e-4:
            continue
        fk = f0 * k * np.sqrt(1 + 0.00012 * k * k)
        tau = decay / (1 + (k - 1) * (0.35 - 0.25 * bright))
        y += a * np.exp(-t / tau) * np.sin(TAU * fk * t + _rng.random() * TAU)
        total += a
    y /= max(total, 1e-6)
    na = int(0.002 * SR)
    y[:na] *= np.linspace(0, 1, na)
    nc = int(0.006 * SR)
    y[:nc] += highpass(noise(nc), 2000) * np.linspace(1, 0, nc) * 0.06 * bright
    if damp is not None and int(damp * SR) < n:
        nd, nr = int(damp * SR), int(0.08 * SR)
        y = y[:nd + nr]
        y[nd:] *= np.linspace(1, 0, len(y) - nd)
    else:
        y *= fade(n, 0, length * 0.25)
    return y * vel


def strings(note, dur, vel=1.0, attack=0.25, release=0.45, voices=4, detune=8.0, cutoff=3000.0, spread=0.7,
            vib=0.003, low_cut=90.0):
    """String section: detuned sawtooth voices with their own vibrato, spread across the stereo field."""
    f0 = hz(note)
    env = adsr(dur, attack, 0.4, 0.9, release)
    n = len(env)
    out = np.zeros((n, 2))
    for v in range(voices):
        side = (v / max(voices - 1, 1)) * 2 - 1
        cents = side * detune + _rng.normal(0, 1.5)
        f = vibrato(f0 * 2 ** (cents / 1200), n, rate=_rng.uniform(4.8, 5.8), depth=vib, delay=0.15, ramp=0.4)
        out += pan2(saw(f, n), side * spread)
    out = highpass(lowpass(out / voices, cutoff), low_cut)
    return out * env[:, None] * vel


def pad(notes, dur, vel=1.0, attack=0.8, release=1.6, cutoff=1400.0):
    out = None
    for nm in notes:
        s = strings(nm, dur, attack=attack, release=release, voices=3, detune=12.0, cutoff=cutoff, spread=0.9,
                    vib=0.0015)
        out = s if out is None else out + s
    return out * vel / len(notes) ** 0.5


def horn(note, dur, vel=1.0, attack=0.08, release=0.3):
    """Warm horn: brighter while the note starts, then it mellows (two filtered copies crossfaded)."""
    f0 = hz(note)
    env = adsr(dur, attack, 0.3, 0.85, release)
    n = len(env)
    t = np.arange(n) / SR
    x = sum(saw(vibrato(f0 * 2 ** (c / 1200), n, rate=5.0, depth=0.0025, delay=0.3, ramp=0.4), n) for c in (-4, 4)) / 2
    dark, bright = lowpass(x, min(f0 * 4, 900)), lowpass(x, min(f0 * 9, 2800))
    b = 0.25 + 0.55 * np.exp(-t / 0.35) * np.clip(t / attack, 0, 1)
    return highpass(dark * (1 - b) + bright * b, 70) * env * vel


def bass(note, dur, vel=1.0, sustain=False, cutoff=380.0):
    f0 = hz(note)
    env = adsr(dur, 0.03, 1.0, 0.8, 0.35) if sustain else adsr(dur, 0.006, 0.3, 0.65, 0.08)
    n = len(env)
    return (0.8 * sine(f0, n, 0.0) + 0.5 * lowpass(saw(f0, n), cutoff)) * env * vel


VOWELS = {"oo": [(320, 1.0, 1.2), (800, 0.35, 1.3), (2300, 0.08, 1.5)],
          "ah": [(730, 1.0, 1.2), (1100, 0.55, 1.3), (2450, 0.2, 1.4)],
          "oh": [(500, 1.0, 1.2), (850, 0.45, 1.3), (2500, 0.1, 1.5)]}


def choir(notes, dur, vel=1.0, vowel="oo", attack=0.8, release=1.6, voices=3):
    """Wordless choir: sawtooth voices shaped by vowel formants, a little out of tune with each other."""
    env = adsr(dur, attack, 0.5, 0.9, release)
    n = len(env)
    out = np.zeros((n, 2))
    for nm in notes:
        f0 = hz(nm)
        for side in (0, 1):
            src = sum(saw(vibrato(f0 * 2 ** (_rng.normal(0, 7) / 1200), n, rate=_rng.uniform(4.3, 5.4), depth=0.005,
                                  delay=0.1, ramp=0.5), n) for _ in range(voices)) / voices
            out[:, side] += sum(g * bandpass(src, fc * (1 - 0.12 * q), fc * (1 + 0.12 * q)) for fc, g, q in VOWELS[vowel])
    return lowpass(out, 3500) * env[:, None] * vel / len(notes) ** 0.5


def bell(note, vel=1.0, decay=2.0, ratio=3.5, index=2.0, octave=0.3, cents=0.0):
    """FM bell: a bright metallic strike that settles into a pure tone."""
    f0 = hz(note) * 2 ** (cents / 1200)
    n = int(min(decay * 3.2, 7.0) * SR)
    t = np.arange(n) / SR
    mod = index * np.exp(-t / 0.18) * np.sin(TAU * ratio * f0 * t)
    y = np.sin(TAU * f0 * t + mod) * np.exp(-t / decay)
    y += octave * np.sin(TAU * 2 * f0 * t) * np.exp(-t / (decay * 0.4))
    na = int(0.0015 * SR)
    y[:na] *= np.linspace(0, 1, na)
    return lowpass(y, 12000) * fade(n, 0, n / SR * 0.25) * vel


def celesta(note, vel=1.0, decay=1.6):
    """Music-box celesta: two slightly detuned bells, one left and one right."""
    left = bell(note, 1.0, decay=decay, ratio=4.0, index=1.4, octave=0.35, cents=-5)
    right = bell(note, 1.0, decay=decay, ratio=4.0, index=1.4, octave=0.35, cents=5)
    return np.stack([left, right], 1) * vel * 0.7


# ------------------------------------------------------------------ drums ---

def kick(vel=1.0, f_hi=140.0, f_lo=48.0, decay=0.45, click=0.25):
    n = int(min(decay * 5, 2.0) * SR)
    t = np.arange(n) / SR
    f = f_lo + (f_hi - f_lo) * np.exp(-t / 0.035)
    y = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / decay)
    nc = int(0.012 * SR)
    y[:nc] += lowpass(noise(nc), 3000) * np.linspace(1, 0, nc) * click
    return y * vel


def taiko(vel=1.0, f0=78.0, decay=0.7):
    n = int(min(decay * 5, 3.0) * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.7 * np.exp(-t / 0.05))
    body = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / decay)
    skin = bandpass(noise(n), 90, 900) * np.exp(-t / 0.09) * 0.6
    slap = highpass(noise(n), 1500) * np.exp(-t / 0.012) * 0.15
    return np.tanh(1.3 * (body + skin + slap)) * vel


def tom(vel=1.0, f0=150.0, decay=0.35):
    n = int(min(decay * 5, 2.0) * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.5 * np.exp(-t / 0.03))
    body = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / decay)
    skin = bandpass(noise(n), 150, 2000) * np.exp(-t / 0.05) * 0.4
    return (body + skin) * vel


def frame_drum(vel=1.0):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    tone = np.sin(TAU * 180 * t) * np.exp(-t / 0.1)
    skin = bandpass(noise(n), 300, 5000) * np.exp(-t / 0.12)
    return (0.6 * tone + skin) * vel


def shaker(vel=1.0, length=0.1):
    n = int(length * SR)
    t = np.arange(n) / SR
    env = np.sin(np.clip(t / 0.02, 0, 1) * np.pi / 2) * np.exp(-np.maximum(t - 0.02, 0) / 0.035)
    return bandpass(noise(n), 3000, 9000) * env * vel


def crash(vel=1.0, decay=2.0, dark=False):
    n = int(min(decay * 4, 6.0) * SR)
    t = np.arange(n) / SR
    y = highpass(noise(n), 3000) * np.exp(-t / decay)
    for f in (3150, 4270, 5330, 6710, 7900, 9120):
        y += 0.05 * np.sign(np.sin(TAU * f * t + _rng.random() * TAU)) * np.exp(-t / (decay * 0.6))
    return (lowpass(y, 6000) if dark else lowpass(y, 9500)) * vel


def swell(dur, vel=1.0):
    """Reverse-cymbal swell that rises into the next section."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = highpass(noise(n), 2500) * (t / dur) ** 3
    nc = int(0.03 * SR)
    y[-nc:] *= np.linspace(1, 0, nc)
    return y * vel


def subdrop(vel=1.0):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    f = 30 + 60 * np.exp(-t / 0.4)
    return np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 1.2) * fade(n, 0.005, 0.2) * vel


# ------------------------------------------------------------- atmosphere ---

def drip(note, vel=1.0):
    """A water drop in a cave: a short tone that bends up quickly."""
    f0 = hz(note)
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.6 * (1 - np.exp(-t / 0.018)))
    y = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.07)
    na = int(0.001 * SR)
    y[:na] *= np.linspace(0, 1, na)
    return y * vel


def drone(notes, dur, vel=1.0, fade_in=3.0, fade_out=3.0, cutoff=320.0):
    """Low, slowly breathing drone: pure tones with a filtered sawtooth under them."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for nm in notes:
        f0 = hz(nm)
        y += sine(f0, n) + 0.35 * sine(2 * f0, n) + 0.6 * lowpass(saw(f0 * 1.002, n), cutoff)
    breathe = 1 + 0.2 * np.sin(TAU * 0.09 * t + _rng.random() * TAU) + 0.1 * np.sin(TAU * 0.23 * t)
    return y * breathe * fade(n, fade_in, fade_out) * vel / len(notes)


def wind(dur, vel=1.0, fade_in=2.0, fade_out=2.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    lfo1 = 0.6 + 0.4 * np.sin(TAU * 0.07 * t + _rng.random() * TAU)
    lfo2 = 0.5 + 0.5 * np.sin(TAU * 0.11 * t + _rng.random() * TAU)
    y = bandpass(noise(n), 250, 1100) * lfo1 + 0.5 * bandpass(noise(n), 700, 2200) * lfo2
    return y * fade(n, fade_in, fade_out) * vel


def bird(vel=1.0, base=3200.0, syllables=3):
    """A small bird: a few quick chirps that sweep up with a trill."""
    parts = []
    for i in range(syllables):
        n = int(_rng.uniform(0.05, 0.09) * SR)
        t = np.arange(n) / SR
        b = base * _rng.uniform(0.9, 1.15)
        f = b * (1 + 0.35 * t / t[-1]) * (1 + 0.06 * np.sin(TAU * 38 * t))
        env = np.sin(np.pi * t / t[-1]) ** 2
        parts.append(np.sin(TAU * np.cumsum(f) / SR) * env)
        parts.append(np.zeros(int(_rng.uniform(0.03, 0.07) * SR)))
    return np.concatenate(parts) * vel


# ---------------------------------------------------------------- effects ---

def reverb_ir(rt60, predelay=0.02, damp=6000.0, early=(), seed=5):
    """Stereo impulse response: decorrelated noise that decays by 60 dB in rt60 seconds, darker as it fades."""
    r = np.random.default_rng(seed)
    n = int(rt60 * 1.1 * SR)
    t = np.arange(n) / SR
    env = 10 ** (-3 * t / rt60)
    brightness = np.exp(-t / (rt60 * 0.25))
    pre = int(predelay * SR)
    ir = np.zeros((n + pre, 2))
    for c in range(2):
        w = r.standard_normal(n)
        tail = (lowpass(w, damp) * brightness + lowpass(w, damp * 0.3) * (1 - brightness)) * env
        nf = int(0.01 * SR)
        tail[:nf] *= np.linspace(0, 1, nf)
        ir[pre:, c] = tail
    for dt, g, p in early:
        i = int(dt * SR)
        ir[i, 0] += g * (1 - p) / 2 * 8
        ir[i, 1] += g * (1 + p) / 2 * 8
    return ir / np.sqrt((ir ** 2).sum(0).mean())


def convolve(x, ir, n):
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:n] for c in range(2)], 1)


def pingpong(x, delay, feedback=0.45, repeats=6, damp=3500.0):
    """Echoes that bounce between left and right, each one a bit darker and quieter."""
    mono = lowpass(x.mean(1), damp)
    out = np.zeros_like(x)
    d = int(delay * SR)
    for i in range(1, repeats + 1):
        k = i * d
        if k >= len(x):
            break
        out[k:, i % 2] += feedback ** i * mono[:-k]
    return out


# ------------------------------------------------------------------ song ---

class Song:
    """Notes on a timeline, mixed straight into one stereo buffer per stem. Times are in seconds; t(bar, beat)
    converts from the music."""

    def __init__(self, bpm, bars, meter=4, tail=12.0):
        self.beat = 60.0 / bpm
        self.bar = meter * self.beat
        self.bars = bars
        self.length = bars * self.bar
        self.n = int(round(self.length * SR))
        self.n_total = self.n + int(tail * SR)
        self.stems = {}
        self.notes = {}

    def t(self, bar, beat=0.0):
        return bar * self.bar + beat * self.beat

    def add(self, stem, time, x, pan=0.0, gain=1.0):
        x = np.asarray(x, float)
        if x.ndim == 1:
            x = pan2(x, pan)
        elif pan:
            x = x * np.array([min(1.0, 1 - pan), min(1.0, 1 + pan)])
        i = int(round(time * SR))
        if i < 0:
            x, i = x[-i:], 0
        if stem not in self.stems:
            self.stems[stem] = np.zeros((self.n_total, 2), np.float32)
        j = min(self.n_total, i + len(x))
        if j > i:
            self.stems[stem][i:j] += x[:j - i] * gain
        self.notes[stem] = self.notes.get(stem, 0) + 1


def active_rms(buf, win=0.4):
    """RMS over the parts of a stem where it actually plays (within 30 dB of its loudest moment)."""
    mono = buf.mean(1)
    w = int(win * SR)
    k = len(mono) // w
    p = (mono[:k * w].reshape(k, w).astype(np.float64) ** 2).mean(1)
    if p.max() <= 0:
        return 1.0
    return float(np.sqrt(p[p > p.max() * 1e-3].mean()))


def mix(song, levels, reverb_sends, ir, delay_sends=None, delay=None, report=True):
    """Balances every stem to its level (dB), sends it to reverb and delay, and folds the tail for looping."""
    dry = np.zeros((song.n_total, 2))
    rev = np.zeros((song.n_total, 2))
    dly = np.zeros((song.n_total, 2))
    for stem in song.stems:
        assert stem in levels, f"no level for stem {stem}"
    for stem, level in levels.items():
        if stem not in song.stems:
            continue
        buf = song.stems[stem].astype(np.float64)
        buf *= 10 ** (level / 20) / active_rms(buf)
        dry += buf
        rev += buf * reverb_sends.get(stem, 0.0)
        if delay_sends:
            dly += buf * delay_sends.get(stem, 0.0)
        if report:
            print(f"   {stem:10} {song.notes[stem]:5} notes   level {level:6.1f} dB   reverb {reverb_sends.get(stem, 0):.2f}")
    if delay_sends and delay:
        echoes = pingpong(dly, *delay)
        dry += echoes
        rev += echoes * 0.6
    out = dry + convolve(rev, ir, song.n_total)
    loop = out[:song.n].copy()
    tail = out[song.n:]
    loop[:len(tail)] += tail
    return loop


def _biquad(kind, fc, q, gain_db=0.0):
    """RBJ cookbook biquads, as used by the loudness standard (ITU-R BS.1770) for K-weighting."""
    w0 = TAU * fc / SR
    alpha = np.sin(w0) / (2 * q)
    c = np.cos(w0)
    if kind == "shelf":
        a = 10 ** (gain_db / 40)
        r = 2 * np.sqrt(a) * alpha
        b = [a * ((a + 1) + (a - 1) * c + r), -2 * a * ((a - 1) + (a + 1) * c), a * ((a + 1) + (a - 1) * c - r)]
        den = [(a + 1) - (a - 1) * c + r, 2 * ((a - 1) - (a + 1) * c), (a + 1) - (a - 1) * c - r]
    else:
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
        den = [1 + alpha, -2 * c, 1 - alpha]
    return np.array(b) / den[0], np.array(den) / den[0]


def lufs(x):
    """Integrated loudness in LUFS (BS.1770: K-weighting, 400 ms blocks, absolute and relative gates)."""
    y = x
    for kind, fc, q, g in (("shelf", 1500.0, 1 / np.sqrt(2), 4.0), ("highpass", 38.0, 0.5, 0.0)):
        b, a = _biquad(kind, fc, q, g)
        y = signal.lfilter(b, a, y, axis=0)
    block, hop = int(0.4 * SR), int(0.1 * SR)
    power = np.array([(y[i:i + block] ** 2).mean(0).sum() for i in range(0, len(y) - block, hop)])
    loud = -0.691 + 10 * np.log10(power + 1e-12)
    gated = power[loud > -70]
    rel = -0.691 + 10 * np.log10(gated.mean()) - 10
    gated = power[(loud > -70) & (loud > rel)]
    return float(-0.691 + 10 * np.log10(gated.mean()))


def master(loop, target=-15.0, ceiling=0.89):
    """Gentle glue compression, loudness (LUFS) and a soft limiter. Works on two copies of the loop, so the
    filters and the compressor are already settled at the loop point and it stays seamless."""
    y = highpass(np.concatenate([loop, loop], 0), 32)
    p = (y ** 2).mean(1)
    a = np.exp(-1 / (0.08 * SR))
    level = np.sqrt(signal.lfilter([1 - a], [1, -a], p) + 1e-12)
    thr = np.percentile(level, 90) * 0.8
    gain = np.where(level > thr, (level / thr) ** (1 / 2.5 - 1), 1.0)
    b = np.exp(-1 / (0.05 * SR))
    gain = signal.lfilter([1 - b], [1, -b], gain)
    y = (y * gain[:, None])[len(loop):]
    out = y
    for _ in range(3):   # the limiter takes a little loudness away, so adjust and try again
        y = y * 10 ** ((target - lufs(out)) / 20)
        out = soft_limit(y, ceiling)
    return out.astype(np.float32)


def soft_limit(y, ceiling=0.89, knee=0.75):
    """Straight through up to knee * ceiling, then a smooth curve that never goes past the ceiling."""
    k = knee * ceiling
    a = np.abs(y)
    over = a > k
    out = y.copy()
    out[over] = np.sign(y[over]) * (k + (ceiling - k) * np.tanh((a[over] - k) / (ceiling - k)))
    return out
