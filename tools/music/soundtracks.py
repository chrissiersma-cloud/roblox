"""Composes and renders the two area soundtracks for the game.

  Forest     bright adventure: flute, harp, pizzicato and driving strings, horns and taiko drums.
             D major, 112 BPM, 48 bars (1:43).
  DarkWoods  dark adventure in a cave: a music box, a low cello ostinato, a ghostly choir, horns, heartbeat
             drums, water drips and a huge cave echo. D minor, 88 BPM, 40 bars (1:49).

Both are seamless loops: the last bar leads back into the first, and the echo and the notes that ring past the
end are laid over the start, so Sound.Looped plays on without a gap or a jump.

    python3 tools/music/soundtracks.py                   # audio/Forest.ogg + .mp3, audio/DarkWoods.ogg + .mp3
    python3 tools/music/soundtracks.py --only forest --wav
"""

import argparse
import os
import sys
import time

import lameenc
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S  # noqa: E402
from synth import SR, Song  # noqa: E402

# ----------------------------------------------------------------- helpers ---

LETTER = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITY = {"": (0, 4, 7), "m": (0, 3, 7)}


def chord(name):
    """'F#' -> (6, (0, 4, 7)), 'Bbm' -> (10, (0, 3, 7)): the root's pitch class and the chord's intervals."""
    pc, i = LETTER[name[0]], 1
    while i < len(name) and name[i] in "#b":
        pc += 1 if name[i] == "#" else -1
        i += 1
    return pc % 12, QUALITY[name[i:]]


def place(pc, lo):
    """The MIDI note with pitch class pc in [lo, lo + 12)."""
    return lo + (pc - lo) % 12


def voicing(name, lo):
    """A close chord (all notes within one octave from lo), so chords move smoothly from one to the next."""
    r, iv = chord(name)
    return sorted(place(r + i, lo) for i in iv)


def root(name, lo):
    return place(chord(name)[0], lo)


def arp_notes(name, lo):
    """Chord tones going up from the root: root, fifth, octave, tenth, twelfth, two octaves, and so on."""
    r, iv = chord(name)
    r = place(r, lo)
    return [r, r + iv[2], r + 12, r + 12 + iv[1], r + 12 + iv[2], r + 24, r + 24 + iv[1]]


def phrase(text, meter=4):
    """'A4 D5 E5:1.5 r:.5 | ...' -> [(beat, note, beats)]. A note lasts 1 beat unless it says :beats, r is a rest,
    | ends a bar (every bar must be full, which catches typing mistakes)."""
    notes, pos = [], 0.0
    for i, bar in enumerate(text.split("|")):
        start = pos
        for tok in bar.split():
            name, _, d = tok.partition(":")
            d = float(d) if d else 1.0
            if name != "r":
                notes.append((pos, name, d))
            pos += d
        if abs(pos - start - meter) > 1e-6:
            raise ValueError(f"bar {i + 1} of '{text[:30]}...' has {pos - start:g} beats")
    return notes


def hum(t, ms=5.0):
    """A player is never exactly on the grid: nudge a time by a few milliseconds."""
    return t + S.rng().normal(0, ms / 1000)


def vary(spread=0.08):
    return 1 + S.rng().uniform(-spread, spread)


def line(song, stem, bar, text, make, pan=0.0, gain=1.0, shift=0, legato=0.96):
    """Plays a melody from bar `bar`. make(midi_note, seconds) renders one note."""
    for beat, name, beats in phrase(text):
        accent = 1.0 if beat % 2 == 0 else 0.9
        note = make(S.midi(name) + shift, beats * song.beat * legato)
        song.add(stem, hum(song.t(bar, beat), 4), note, pan, gain * accent * vary(0.05))


class RoundRobin:
    """Keeps up to `takes` renders of every note, like a sample library, and plays them in turn."""

    def __init__(self, takes=3):
        self.takes, self.store, self.turn = takes, {}, {}

    def __call__(self, fn, *args, **kw):
        key = (fn.__name__, args, tuple(sorted(kw.items())))
        takes = self.store.setdefault(key, [])
        i = self.turn.get(key, 0)
        self.turn[key] = i + 1
        if len(takes) < self.takes:
            takes.append(fn(*args, **kw))
        return takes[i % self.takes]


def sections(song, marks):
    """[(name, first_bar, energy)] -> the section name and the energy (0..1) of every bar."""
    names, energy = [], []
    for i, (name, start, e) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else song.bars
        names += [name] * (end - start)
        energy += [e] * (end - start)
    return names, energy


def looped(song, stem, x, xf, pan=0.0, gain=1.0):
    """A sound that runs through the whole loop. It is xf seconds longer than the song: its end fades out while
    its start fades in, and once the tail is folded onto the start those two crossfade at the loop point."""
    k = int(xf * SR)
    w = np.ones(len(x))
    w[:k] = np.sin(np.linspace(0, np.pi / 2, k))
    w[-k:] = np.cos(np.linspace(0, np.pi / 2, k))
    song.add(stem, 0.0, x * (w[:, None] if x.ndim == 2 else w), pan, gain)


# ------------------------------------------------------------------ Forest ---

FOREST_CHORDS = ("D G D A | D A Bm G D A G A | D A Bm G D A G A | Bm G D A Bm G Em F# | "
                 "G D Em A G D Em A | D A Bm G D A G A | D G Em A")

# The main theme, on the flute (and in the last A on flute, violins, horns and glockenspiel together).
FOREST_A = ("A4 D5 E5 F#5 | E5:1.5 D5:.5 C#5 A4 | B4 D5 F#5:1.5 E5:.5 | D5:2 B4 A4 | "
            "A4 D5 E5 F#5 | A5:1.5 G5:.5 F#5 E5 | D5 E5:.5 F#5:.5 G5 B4 | C#5 E5 A5:2")
# The bridge, on the violins.
FOREST_B = ("F#5:2 D5 B4 | G5:2 F#5 E5 | F#5:1.5 E5:.5 D5 A4 | E5:3 C#5 | "
            "D5 F#5 B5:2 | A5 G5 F#5 E5 | G5:1.5 F#5:.5 E5 D5 | C#5:2 A#4:2")
# A horn call that opens the track (and opens it again every time it loops).
FOREST_CALL = "D4:1.5 A4:.5 D5:2 | B4:1.5 A4:.5 G4:2 | F#4:1.5 E4:.5 D4:2 | E4:4"
# The quiet part: the horn sings, the flute answers.
FOREST_C_HORN = "D4 G4 B4:1.5 A4:.5 | A4:2 F#4 D4 | E4 G4 B4 E5 | C#5:3 A4"
FOREST_C_FLUTE = "D6:1.5 B5:.5 G5 B5 | A5:1.5 F#5:.5 D5:2 | G5 F#5 E5 G5 | A5:3 r"
FOREST_OUTRO = "A4 D5 E5 F#5 | G5:2 F#5 E5 | E5:3 D5 | C#5:4"
# Horn chords under the second A and under the bridge.
FOREST_HORNS_A2 = ("F#4:4 | E4:4 | F#4:4 | G4:4 | F#4:4 | E4:4 | D4:4 | E4:4",
                   "D4:4 | C#4:4 | D4:4 | D4:4 | A3:4 | A3:4 | B3:4 | C#4:4")
FOREST_HORNS_B = ("D4:4 | D4:4 | D4:4 | C#4:4 | D4:4 | D4:4 | E4:4 | C#4:4",
                  "B3:4 | B3:4 | A3:4 | A3:4 | B3:4 | B3:4 | B3:4 | A#3:4")

HARP_8 = [0, 1, 2, 3, 4, 3, 2, 1]
HARP_16 = [0, 1, 2, 3, 4, 5, 4, 3, 2, 3, 4, 5, 6, 5, 4, 3]
GALLOP = [(0, 1.0), (0, .55), (12, .7), (0, .95), (0, .55), (12, .7), (0, .9), (7, .6)]   # 3+3+2 accents


def forest():
    S.reseed(112)
    rnd, rr = S.rng(), RoundRobin()
    song = Song(bpm=112, bars=48)
    t = song.t
    chords = FOREST_CHORDS.replace("|", " ").split()
    assert len(chords) == song.bars
    sec, energy = sections(song, [("intro", 0, .55), ("a1", 4, .7), ("a2", 12, .82), ("b", 20, .92),
                                  ("c", 28, .55), ("a3", 36, 1.0), ("outro", 44, .6)])
    energy[34], energy[35] = .65, .8   # the quiet part builds up into the last A

    def harp(n, vel):
        return rr(S.pluck, int(n), decay=1.6, pos=0.18, bright=0.55) * vel

    def pizz(n, vel):
        return rr(S.pluck, int(n), decay=0.45, pos=0.3, bright=0.35, damp=0.25) * vel

    def spiccato(n, vel):
        return rr(S.strings, int(n), 0.16, attack=0.008, release=0.1, voices=3, detune=6.0, cutoff=2200.0,
                  spread=0.3, vib=0.0, low_cut=60.0) * vel

    def flute(n, d):
        return S.flute(n, d)

    def violins(n, d):
        return S.strings(n, d, attack=0.08, release=0.35, voices=5, detune=7.0, cutoff=4200.0, spread=0.5, vib=0.004)

    def horn(n, d):
        return S.horn(n, d)

    def horn_pad(n, d):
        return S.horn(n, d, attack=0.25, release=0.5)

    def glock(n, d):
        return rr(S.bell, int(n), decay=1.0, ratio=3.5, index=1.2, octave=0.25)

    # Melodies.
    line(song, "horns", 0, FOREST_CALL, horn, pan=.25, gain=.7)
    line(song, "flute", 4, FOREST_A, flute, pan=.1)
    for text in FOREST_HORNS_A2:
        line(song, "horns", 12, text, horn_pad, pan=.3, gain=.55)
    line(song, "flute", 12, FOREST_A, flute, pan=.1)
    line(song, "violins", 20, FOREST_B, violins, pan=-.25)
    for text in FOREST_HORNS_B:
        line(song, "horns", 20, text, horn_pad, pan=.3, gain=.6)
    line(song, "horns", 28, FOREST_C_HORN, horn, pan=.2, gain=.85)
    line(song, "flute", 32, FOREST_C_FLUTE, flute, pan=.1, gain=.85)
    line(song, "flute", 36, FOREST_A, flute, pan=.1)
    line(song, "violins", 36, FOREST_A, violins, pan=-.25, gain=.8)
    line(song, "horns", 36, FOREST_A, horn, pan=.25, shift=-12, gain=.85)
    line(song, "glock", 36, FOREST_A, glock, pan=-.15, shift=12)
    line(song, "flute", 44, FOREST_OUTRO, flute, pan=.1, gain=.75)

    for bar, ch in enumerate(chords):
        s, e = sec[bar], energy[bar]

        # Strings holding the chord, a low bass note, and the harp rolling underneath.
        song.add("pad", t(bar), S.pad(voicing(ch, 57), song.bar * 1.02, vel=e, attack=0.5, release=1.2,
                                      cutoff=1200 + 1600 * e))
        song.add("bass", t(bar), S.bass(root(ch, 38), song.bar * 0.97, vel=e, sustain=True))
        tones = arp_notes(ch, 43)
        pattern, step = (HARP_16, .25) if s in ("a2", "a3") else (HARP_8, .5)
        for i, k in enumerate(pattern):
            accent = 1.0 if (i * step) % 1 == 0 else .72
            song.add("harp", hum(t(bar, i * step)), harp(tones[k], e * accent * vary() * (.8 if step < .5 else 1)),
                     -.35)

        # Pizzicato: a bass note on 1 and 3 and short chords on 2 and 4.
        if s in ("a1", "c", "outro"):
            r = root(ch, 45)
            song.add("pizz", hum(t(bar, 0)), pizz(r, e), .3)
            if s != "outro":
                song.add("pizz", hum(t(bar, 2)), pizz(r + 7, e * .8), .3)
                for beat in (1, 3):
                    for j, n in enumerate(voicing(ch, 62)):
                        song.add("pizz", hum(t(bar, beat)) + j * .012, pizz(n, e * .5 * vary()), .45)

        # The galloping low strings that drive the adventure.
        if s in ("a2", "b", "a3") or bar in (34, 35):
            r = root(ch, 40)
            for i, (k, vel) in enumerate(GALLOP):
                song.add("lowstr", hum(t(bar, i / 2), 4), spiccato(r + k, vel * e * vary()), .15)

        # Drums.
        taiko = []
        if s == "a1":
            taiko = [(0, 1.0), (2.5, .5)]
        elif s == "a2":
            taiko = [(0, 1.0), (1.5, .45), (2, .8), (3.5, .55)]
        elif s in ("b", "a3"):
            taiko = [(0, 1.0), (.5, .45), (1.5, .6), (2, .9), (3, .65), (3.5, .6)]
        elif s == "outro" and bar < 47:
            taiko = [(0, .8)]
        elif bar == 3:
            taiko = [(2, .45), (3, .6), (3.5, .8)]
        for beat, vel in taiko:
            song.add("taiko", hum(t(bar, beat), 3), rr(S.taiko, f0=78.0 if beat % 1 == 0 else 96.0) * vel * e)
        if s in ("a1", "a2", "b", "a3"):
            for beat in (1, 3):
                song.add("frame", hum(t(bar, beat), 3), rr(S.frame_drum) * e * vary(), -.2)
        elif s == "c":
            song.add("frame", hum(t(bar, 0), 3), rr(S.frame_drum) * .5 * vary(), -.2)
        if s in ("a1", "a2", "b", "a3") or bar in (2, 3, 34, 35, 44, 45):
            for i in range(8):
                song.add("shaker", hum(t(bar, i / 2), 6), rr(S.shaker) * (1.0 if i % 2 else .6) * vary(.15), .4)

    # Tom fills at the ends of sections, cymbals at the starts.
    fills = {19: [(2, .5, 200), (2.5, .6, 170), (3, .75, 140), (3.5, .9, 115)],
             27: [(2 + i / 4, .45 + .07 * i, (220, 180, 150, 120)[i // 2]) for i in range(8)],
             35: [(i / 4, .25 + .05 * i, 170 if i % 2 else 130) for i in range(16)],
             43: [(3, .6, 170), (3.5, .75, 125)]}
    for bar, hits in fills.items():
        for beat, vel, f0 in hits:
            song.add("toms", hum(t(bar, beat), 3), rr(S.tom, f0=float(f0)) * vel, .2 if f0 > 150 else -.2)
    for bar, vel in ((4, .45), (12, .8), (20, .9), (36, 1.0)):
        song.add("cym", t(bar), S.crash(vel), .1)
    for bar, beats in ((11, 2), (19, 4), (35, 4)):
        song.add("cym", t(bar, 4 - beats), S.swell(beats * song.beat, .8))

    # Birds in the quiet parts.
    for bar in [0, 1, 2, 3] + list(range(28, 36)) + [44, 45, 46]:
        if rnd.random() < .6:
            song.add("birds", t(bar, rnd.uniform(0, 4)),
                     S.bird(rnd.uniform(.5, 1), base=rnd.uniform(2600, 4200), syllables=int(rnd.integers(2, 5))),
                     rnd.uniform(-.8, .8))

    return dict(
        song=song,
        levels={"flute": -15, "violins": -16, "horns": -19, "glock": -29, "harp": -21, "pizz": -22, "pad": -25,
                "bass": -23, "lowstr": -21, "taiko": -18.5, "frame": -25, "shaker": -31, "toms": -21, "cym": -27,
                "birds": -30},
        reverb={"flute": .3, "violins": .35, "horns": .4, "glock": .45, "harp": .3, "pizz": .25, "pad": .45,
                "bass": .04, "lowstr": .12, "taiko": .2, "frame": .18, "shaker": .12, "toms": .22, "cym": .3,
                "birds": .5},
        ir=S.reverb_ir(2.2, predelay=0.018, damp=7500.0, early=[(.011, .5, -.5), (.019, .4, .6), (.027, .3, -.2)]),
        delay_sends={"flute": .12, "glock": .25, "harp": .06},
        delay=(song.beat * .75, .35, 4, 4000.0),
    )


# -------------------------------------------------------------- Dark Woods ---

DARK_CHORDS = ("Dm Dm Bb A | Dm Bb Gm A Dm Bb Gm A | Dm C Bb A Dm C Bb A | Dm Eb Dm Eb Bb Gm Eb A | "
               "Dm C Bb A Dm C Bb A | Dm Bb Gm A")

# The music box theme.
DARK_A = ("D5 F5 A5 G5:.5 F5:.5 | E5:1.5 F5:.5 D5:2 | G4 Bb4 D5 C5:.5 Bb4:.5 | A4:2 C#5 E5 | "
          "D5 F5 A5 C6 | Bb5:1.5 A5:.5 G5 F5 | E5 G5 Bb5:.5 A5:.5 G5 | C#5 E5 A4:2")
# The adventure theme: low horns and violas, later violins an octave up.
DARK_B = ("D4:.5 F4:.5 A4:2 G4:.5 F4:.5 | E4:1.5 F4:.5 G4:2 | F4 D4 Bb3 D4 | C#4 E4 A4:2 | "
          "D5:1.5 C5:.5 A4 F4 | G4 E4 C5:2 | Bb4 A4 G4 F4 | E4 C#4 A3:2")
DARK_INTRO = "r:4 | r:4 | A5:1.5 G5:.5 F5 D5 | E5:3 r"
DARK_CALL = "r:2 A3:1.5 D4:.5 | F4:1.5 E4:.5 D4:2 | r:4 | r:4"    # a horn far away in the cave
DARK_C_BELLS = "D6:2 A5:2 | G5:2 Eb5:2 | D6:2 A5:2 | Bb5:2 G5:2 | F5:2 D5:2 | G5:2 Bb4:2 | G5:2 Eb5:2 | E5:2 C#5:2"
DARK_OUTRO = "D5 F5 A5 G5:.5 F5:.5 | E5:1.5 F5:.5 D5:2 | G4 Bb4 D5 C5:.5 Bb4:.5 | A4:4"

OSTINATO = [(0, 1.0), (0, .6), (7, .75), (0, .6), (12, .85), (0, .6), (7, .75), (0, .65)]
DRIP_NOTES = [86, 89, 91, 93, 96, 98]    # D minor pentatonic, high up: D6 F6 G6 A6 C7 D7


def dark_woods():
    S.reseed(88)
    rnd, rr = S.rng(), RoundRobin()
    song = Song(bpm=88, bars=40)
    t = song.t
    chords = DARK_CHORDS.replace("|", " ").split()
    assert len(chords) == song.bars
    sec, energy = sections(song, [("intro", 0, .5), ("a", 4, .65), ("b", 12, .85), ("c", 20, .5), ("b2", 28, 1.0),
                                  ("outro", 36, .55)])
    energy[24:28] = [.6, .7, .8, .9]   # the cave part builds up into the last B

    def celesta(n, d, decay=1.8):
        return rr(S.celesta, int(n), decay=decay)

    def harp(n, vel):
        return rr(S.pluck, int(n), decay=2.2, pos=0.22, bright=0.3) * vel

    def cello(n, vel):
        return rr(S.strings, int(n), 0.2, attack=0.01, release=0.12, voices=3, detune=6.0, cutoff=1600.0,
                  spread=0.3, vib=0.0, low_cut=55.0) * vel

    def horn(n, d):
        return S.horn(n, d)

    def violas(n, d):
        return S.strings(n, d, attack=0.1, release=0.4, voices=4, detune=7.0, cutoff=2600.0, spread=0.5, vib=0.004)

    def violins(n, d):
        return S.strings(n, d, attack=0.08, release=0.4, voices=5, detune=7.0, cutoff=3600.0, spread=0.5, vib=0.0045)

    def heart(vel):
        return rr(S.kick, f_hi=95.0, f_lo=42.0, decay=0.22, click=0.05) * vel

    # Melodies.
    line(song, "horns", 0, DARK_CALL, horn, pan=-.3, gain=.45)
    line(song, "celesta", 0, DARK_INTRO, celesta, gain=.8)
    line(song, "celesta", 4, DARK_A, celesta)
    line(song, "horns", 12, DARK_B, horn, pan=-.2)
    line(song, "violas", 12, DARK_B, violas, pan=.2)
    line(song, "celesta", 20, DARK_C_BELLS, lambda n, d: celesta(n, d, 2.6), gain=.75)
    line(song, "violins", 28, DARK_B, violins, pan=.2, shift=12)
    line(song, "horns", 28, DARK_B, horn, pan=-.2)
    line(song, "celesta", 36, DARK_OUTRO, celesta, gain=.85)

    for bar, ch in enumerate(chords):
        s, e = sec[bar], energy[bar]
        cave_start = s == "c" and bar < 24

        # Low strings holding the chord, the bass, and a dark harp.
        if bar >= 2 and not cave_start:
            song.add("pad", t(bar), S.pad(voicing(ch, 50), song.bar * 1.02, vel=e, attack=0.7, release=1.5,
                                          cutoff=700 + 900 * e))
        if s != "intro" and not cave_start:
            song.add("bass", t(bar), S.bass(root(ch, 38), song.bar * 0.97, vel=e, sustain=True, cutoff=260.0))
        if s in ("a", "b", "b2", "outro") or bar >= 24 and s == "c":
            tones = arp_notes(ch, 45)
            for i, k in enumerate(HARP_8):
                song.add("harp", hum(t(bar, i / 2)), harp(tones[k], e * (1.0 if i % 2 == 0 else .7) * vary()), -.3)

        # A soft music-box arpeggio high above the last B.
        if s == "b2":
            r, iv = chord(ch)
            r = place(r, 74)
            tones = [r, r + iv[1], r + iv[2], r + 12]
            for i, k in enumerate([0, 1, 2, 3, 2, 1, 2, 1]):
                song.add("celesta", hum(t(bar, i / 2)), celesta(tones[k], 0) * .4 * vary(), .35 if i % 2 else -.35)

        # The choir: "oo" when it is mysterious, "ah" for the adventure, "oh" deep in the cave.
        vowel = {"intro": "oo", "a": "oo", "b": "ah", "c": "oh", "b2": "ah", "outro": "oo"}[s]
        if s in ("b", "c", "b2", "outro") or s == "a" and bar >= 8:
            song.add("choir", t(bar), S.choir(voicing(ch, 55), song.bar * 1.0, vel=e, vowel=vowel, attack=0.9,
                                              release=1.8))
        elif bar in (0, 2, 3):
            length = 2 if bar == 0 else 1
            song.add("choir", t(bar), S.choir(voicing(ch, 55), song.bar * length, vel=.6, vowel="oo", attack=1.5,
                                              release=2.0))

        # The cello ostinato that keeps the adventure moving.
        if s in ("b", "b2") or bar >= 24 and s == "c":
            r = root(ch, 45)
            for i, (k, vel) in enumerate(OSTINATO):
                song.add("cello", hum(t(bar, i / 2), 4), cello(r + k, vel * e * vary()), .15)

        # Drums: a slow heartbeat when it is tense, taiko when the adventure starts.
        if s == "a" or (s == "c" and bar < 26) or bar in (36, 37):
            for beat in (0, 2):
                song.add("heart", t(bar, beat), heart(e))
                song.add("heart", t(bar, beat) + .24, heart(e * .7))
        taiko = []
        if bar in (0, 2):
            taiko = [(0, .9 if bar == 0 else .6)]
        elif s == "a" and bar in (4, 8):
            taiko = [(0, .7)]
        elif s in ("b", "b2"):
            taiko = [(0, 1.0), (1.5, .5), (2, .75), (3, .45), (3.5, .6)]
        elif bar == 24:
            taiko = [(0, .7)]
        elif bar == 25:
            taiko = [(0, .7), (2, .6)]
        elif bar == 26:
            taiko = [(0, .8), (1.5, .5), (2, .7), (3.5, .6)]
        elif bar == 27:
            taiko = [(i / 2, .4 + .08 * i) for i in range(8)]
        elif bar == 36:
            taiko = [(0, .6)]
        for beat, vel in taiko:
            song.add("taiko", hum(t(bar, beat), 3), rr(S.taiko, f0=70.0 if beat % 1 == 0 else 88.0) * vel)

    fills = {15: [(3, .6, 150), (3.5, .7, 120)],
             19: [(2, .5, 170), (2.5, .6, 150), (3, .7, 130), (3.5, .8, 110)],
             27: [(i / 4, .3 + .045 * i, 150 if i % 2 else 120) for i in range(16)],
             31: [(3, .6, 150), (3.5, .7, 120)],
             35: [(2, .5, 170), (2.5, .6, 150), (3, .7, 130), (3.5, .8, 110)]}
    for bar, hits in fills.items():
        for beat, vel, f0 in hits:
            song.add("toms", hum(t(bar, beat), 3), rr(S.tom, f0=float(f0), decay=0.45) * vel, .25 if f0 > 135 else -.25)
    for bar, vel in ((12, .7), (28, 1.0), (32, .7)):
        song.add("cym", t(bar), S.crash(vel, decay=2.5, dark=True), -.1)
    for bar, beats in ((11, 2), (27, 4)):
        song.add("cym", t(bar, 4 - beats), S.swell(beats * song.beat, .8))

    # Deep in the cave: bells tolling, the ground rumbling.
    for bar, note in ((20, "D3"), (22, "D3"), (24, "Bb2"), (26, "Eb3")):
        song.add("bells", t(bar), S.bell(note, decay=4.0, ratio=1.4, index=2.5, octave=0.4), .15)
    for bar, vel in ((0, .6), (20, 1.0), (24, .8), (28, 1.0)):
        song.add("sub", t(bar), S.subdrop(vel))

    # The cave itself: a low drone, moving air and water dripping from the ceiling.
    xf = 4.0
    looped(song, "drone", S.drone(["D2", "A2"], song.length + xf, fade_in=0, fade_out=0), xf)
    looped(song, "wind", S.wind(song.length + xf, fade_in=0, fade_out=0), xf)
    for b0, b1, gap in ((0, 4, 1.1), (4, 12, 1.6), (12, 20, 2.4), (20, 28, .7), (28, 36, 2.4), (36, 40, 1.1)):
        when = t(b0) + rnd.exponential(gap)
        while when < t(b1):
            song.add("drips", when, S.drip(int(rnd.choice(DRIP_NOTES)), vel=rnd.uniform(.35, 1.0)), rnd.uniform(-.8, .8))
            when += rnd.exponential(gap) + .15

    return dict(
        song=song,
        levels={"celesta": -19, "harp": -22, "cello": -19, "horns": -17.5, "violins": -18, "violas": -21,
                "choir": -22, "pad": -26, "bass": -23, "drone": -25, "wind": -34, "drips": -27, "taiko": -18,
                "heart": -21, "toms": -21, "cym": -28, "bells": -23, "sub": -22},
        reverb={"celesta": .55, "harp": .45, "cello": .22, "horns": .5, "violins": .45, "violas": .4, "choir": .7,
                "pad": .6, "bass": .04, "drone": .25, "wind": .5, "drips": .9, "taiko": .45, "heart": .15,
                "toms": .4, "cym": .5, "bells": .7, "sub": .05},
        ir=S.reverb_ir(5.5, predelay=0.035, damp=4200.0,
                       early=[(.043, .5, -.6), (.071, .4, .7), (.113, .35, -.3), (.167, .3, .5), (.231, .25, -.8),
                              (.307, .2, .2)]),
        delay_sends={"celesta": .28, "drips": .35, "bells": .2, "horns": .08},
        delay=(song.beat * .75, .45, 6, 3000.0),
    )


# ------------------------------------------------------------------ export ---

TRACKS = {"forest": ("Forest", forest), "darkwoods": ("DarkWoods", dark_woods)}


def render(build, target=-15.0):
    parts = build()
    song = parts["song"]
    loop = S.mix(song, parts["levels"], parts["reverb"], parts["ir"], parts["delay_sends"], parts["delay"])
    return S.master(loop, target), song


def export(name, audio, outdir, wav=False):
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, name)
    # libsndfile's Vorbis encoder crashes when it gets a long file in one go, so feed it in blocks.
    with sf.SoundFile(base + ".ogg", "w", SR, 2, format="OGG", subtype="VORBIS", compression_level=0.35) as f:
        for i in range(0, len(audio), 8192):
            f.write(audio[i:i + 8192])
    pcm = (np.clip(audio, -1, 1) * 32767).round().astype("<i2")
    enc = lameenc.Encoder()
    enc.set_bit_rate(192)
    enc.set_in_sample_rate(SR)
    enc.set_channels(2)
    enc.set_quality(2)
    with open(base + ".mp3", "wb") as f:
        f.write(enc.encode(pcm.tobytes()) + enc.flush())
    if wav:
        sf.write(base + ".wav", pcm, SR, subtype="PCM_16")
    return [base + ext for ext in (".ogg", ".mp3") + ((".wav",) if wav else ())]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=sorted(TRACKS))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "audio"))
    ap.add_argument("--wav", action="store_true", help="also write an uncompressed .wav")
    args = ap.parse_args()
    for key, (name, build) in TRACKS.items():
        if args.only and key != args.only:
            continue
        start = time.time()
        print(f"{name}:")
        audio, song = render(build)
        files = export(name, audio, os.path.normpath(args.out), args.wav)
        peak = 20 * np.log10(np.abs(audio).max())
        print(f"   {song.length:.1f} s, {S.lufs(audio):.1f} LUFS, peak {peak:.1f} dBFS, {time.time() - start:.0f} s to make")
        for f in files:
            print(f"   -> {os.path.relpath(f)} ({os.path.getsize(f) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
