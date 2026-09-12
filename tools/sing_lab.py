#!/usr/bin/env python3
"""Interactive lab for Singing Oracle melody strategies.

Requires the passthrough firmware (any commit at or after e89bb75) and
pyserial. Type `help` in the REPL to list commands.

Quick tour:
    strategies                # list available generators
    hello there               # play the current strategy on 'hello there'
    use rhythmic              # switch to a different strategy
    hello there               # same text, new sound
    demo hello there          # play the phrase under EVERY strategy in order
    texts                     # play the curated TEST_TEXTS under current strategy
    matrix                    # play EVERY test text under EVERY strategy (long)
    names matthijs bruce alice sam
    compare wide arpeggio matthijs is home
    set dur_max=600           # tweak a config field
    set arpeggios=true
    patch 54                  # try Voice Oohs instead of Choir Aahs
    show                      # dump current config
    quit
"""

import cmd
import hashlib
import random
import sys
import time
from dataclasses import dataclass, replace

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial required: pip install pyserial")

# ---------------------------------------------------------------- constants --

ATOMS3_VID, ATOMS3_PID = 0x303A, 0x1001
CHOIR_AAHS = 0x34
C_MAJOR = [0, 2, 4, 5, 7, 9, 11]  # semitones from root


# ------------------------------------------------------------------ helpers --

def find_port() -> str:
    for p in list_ports.comports():
        if p.vid == ATOMS3_VID and p.pid == ATOMS3_PID:
            return p.device
    sys.exit("no AtomS3 found; plug it in and re-run")


def syllables(word: str) -> int:
    vowels = set("aeiouyAEIOUY")
    n, in_v = 0, False
    for c in word:
        if c in vowels:
            if not in_v:
                n += 1
                in_v = True
        else:
            in_v = False
    return max(n, 1)


def seed_of(text: str) -> int:
    return int(hashlib.sha1(text.encode()).hexdigest()[:8], 16)


def in_scale(root: int, i: int) -> int:
    """MIDI note for scale index i (can be negative or > len(scale))."""
    octaves, degree = divmod(i, len(C_MAJOR))
    return root + 12 * octaves + C_MAJOR[degree]


# --------------------------------------------------------------- data types --

@dataclass
class Config:
    root: int = 60            # C4
    dur_min: int = 220
    dur_max: int = 400
    step_max: int = 2         # max stepwise jump in scale degrees
    range_low: int = -3       # scale-index bounds
    range_high: int = 10
    patch: int = CHOIR_AAHS
    velocity: int = 100
    gap_ms: int = 20          # inter-note pause
    final_stretch: float = 1.5


# ----------------------------------------------------------------- cadence --

def cadence(notes, text, cfg):
    """Nudge the last note down for statements, up for questions."""
    if len(notes) < 2:
        return
    is_q = text.rstrip().endswith('?')
    last_pitches, last_dur = notes[-1]
    prev = notes[-2][0][0]
    shift = 0
    if is_q and last_pitches[0] <= prev:
        shift = +2
    elif not is_q and last_pitches[0] >= prev:
        shift = -2
    if shift:
        notes[-1] = ([n + shift for n in last_pitches], last_dur)


# ------------------------------------------------------------- strategies --

def gen_baseline(text, cfg):
    """The current sing.py behaviour: stepwise random walk in C major."""
    rng = random.Random(seed_of(text))
    n = sum(syllables(w) for w in text.split()) or 1
    idx = rng.randint(cfg.range_low + 2, cfg.range_high - 2)
    out = []
    for i in range(n):
        idx = max(cfg.range_low, min(cfg.range_high, idx + rng.randint(-cfg.step_max, cfg.step_max)))
        dur = rng.randint(cfg.dur_min, cfg.dur_max)
        if i == n - 1:
            dur = int(dur * cfg.final_stretch)
        out.append(([in_scale(cfg.root, idx)], dur))
    cadence(out, text, cfg)
    return out


def gen_wide(text, cfg):
    """Wider range, ~30% chance of leaping a 3rd or 5th instead of stepwise."""
    rng = random.Random(seed_of(text))
    n = sum(syllables(w) for w in text.split()) or 1
    idx = rng.randint(cfg.range_low + 2, cfg.range_high - 2)
    out = []
    for i in range(n):
        if rng.random() < 0.3:
            idx += rng.choice([-4, -2, 2, 4])
        else:
            idx += rng.randint(-cfg.step_max, cfg.step_max)
        idx = max(cfg.range_low, min(cfg.range_high, idx))
        dur = rng.randint(cfg.dur_min, cfg.dur_max)
        if i == n - 1:
            dur = int(dur * cfg.final_stretch)
        out.append(([in_scale(cfg.root, idx)], dur))
    cadence(out, text, cfg)
    return out


def gen_rhythmic(text, cfg):
    """Fixed rhythmic template selected by hash — same name = same rhythm."""
    patterns = [
        [200, 200, 400],           # trochee-ish
        [150, 300],                # iamb
        [400, 200, 200, 400],      # dotted
        [250, 250, 250, 500],      # steady + long ending
        [180, 180, 180, 540],      # dactyl
        [300, 150, 150, 300],      # arch
    ]
    rng = random.Random(seed_of(text))
    n = sum(syllables(w) for w in text.split()) or 1
    pat = patterns[seed_of(text) % len(patterns)]
    durs = [pat[i % len(pat)] for i in range(n)]
    idx = rng.randint(cfg.range_low + 2, cfg.range_high - 2)
    out = []
    for i, dur in enumerate(durs):
        idx = max(cfg.range_low, min(cfg.range_high, idx + rng.randint(-cfg.step_max, cfg.step_max)))
        if i == n - 1:
            dur = int(dur * cfg.final_stretch)
        out.append(([in_scale(cfg.root, idx)], dur))
    cadence(out, text, cfg)
    return out


def gen_arpeggio(text, cfg):
    """Notes land on triad tones of a I-V-IV-I progression."""
    triads = {'I': [0, 2, 4], 'IV': [3, 5, 0], 'V': [4, 6, 1]}
    progression = ['I', 'V', 'IV', 'I']
    rng = random.Random(seed_of(text))
    n = sum(syllables(w) for w in text.split()) or 1
    out = []
    for i in range(n):
        chord = triads[progression[i % len(progression)]]
        idx = rng.choice(chord)
        if rng.random() < 0.2:
            idx += 7 * rng.choice([-1, 1])   # occasional octave leap
        dur = rng.randint(cfg.dur_min, cfg.dur_max)
        if i == n - 1:
            dur = int(dur * cfg.final_stretch)
        out.append(([in_scale(cfg.root, idx)], dur))
    cadence(out, text, cfg)
    return out


def gen_formant(text, cfg):
    """Two-note chords approximating vowel formants (F1 + F2).

    Not real speech — just a wild proof of what pure-MIDI can suggest.
    """
    # F1/F2 approximations for English vowels, mapped to nearest MIDI notes.
    vowels = {
        'a': [74, 86],   # 'ah'
        'e': [72, 92],   # 'eh'
        'i': [62, 96],   # 'ee'
        'o': [69, 82],   # 'oh'
        'u': [67, 78],   # 'oo'
    }
    def vowel_of(word):
        for c in word.lower():
            if c in vowels:
                return c
        return 'a'
    rng = random.Random(seed_of(text))
    out = []
    for w in (text.split() or [text]):
        v = vowels[vowel_of(w)]
        n = syllables(w)
        for i in range(n):
            dur = rng.randint(cfg.dur_min, cfg.dur_max)
            if i == n - 1:
                dur = int(dur * cfg.final_stretch)
            out.append((list(v), dur))
    return out


STRATEGIES = {
    'baseline': gen_baseline,
    'wide': gen_wide,
    'rhythmic': gen_rhythmic,
    'arpeggio': gen_arpeggio,
    'formant': gen_formant,
}

# Curated evaluation set — short, varied, covers the ways the Oracle will be
# called in real life: names (leitmotif recognisability), greetings, questions,
# notifications, single words, longer phrases.
TEST_TEXTS = [
    "matthijs",
    "bruce",
    "hello",
    "welcome home",
    "did you lock the door?",
    "package arrived",
    "the weather turned",
    "front door opened",
]


# -------------------------------------------------------------- playback --

def play(port: str, notes, cfg: Config) -> None:
    with serial.Serial(port, 115200, timeout=1) as s:
        s.dtr = False
        s.rts = False
        time.sleep(0.1)
        s.write(bytes([0xC0, cfg.patch]))
        time.sleep(0.05)
        for pitches, dur in notes:
            for n in pitches:
                s.write(bytes([0x90, n, cfg.velocity]))
            time.sleep(dur / 1000)
            for n in pitches:
                s.write(bytes([0x80, n, 0x00]))
            time.sleep(cfg.gap_ms / 1000)


def render(text: str, strategy: str, cfg: Config):
    notes = STRATEGIES[strategy](text, cfg)
    pretty = ", ".join(f"{'+'.join(str(n) for n in p)}@{d}" for p, d in notes)
    print(f"  [{strategy}] {pretty}")
    return notes


# ----------------------------------------------------------------- REPL --

class Lab(cmd.Cmd):
    intro = ("\nSinging Oracle Lab. Type text to hear it. `help` for commands.\n"
             "Every port-open pulses the AtomS3 firmware's boot beep, so expect a\n"
             "brief middle-C before each phrase.\n")
    prompt = "sing> "

    def __init__(self, port: str) -> None:
        super().__init__()
        self.port = port
        self.cfg = Config()
        self.strategy = 'baseline'

    def default(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        play(self.port, render(line, self.strategy, self.cfg), self.cfg)

    def do_strategies(self, _):
        """List available melody strategies."""
        for name in STRATEGIES:
            marker = "*" if name == self.strategy else " "
            print(f"  {marker} {name}")

    def do_use(self, arg: str):
        """use <strategy>  — switch active strategy"""
        arg = arg.strip()
        if arg not in STRATEGIES:
            print(f"unknown; pick: {', '.join(STRATEGIES)}")
            return
        self.strategy = arg
        print(f"strategy = {arg}")

    def do_demo(self, arg: str):
        """demo [phrase]  — play the phrase under every strategy in order"""
        text = arg.strip() or "hello there"
        for name in STRATEGIES:
            print(f"\n=== {name} ===")
            play(self.port, render(text, name, self.cfg), self.cfg)
            time.sleep(0.6)

    def do_names(self, arg: str):
        """names alice bob carol  — play each name under the current strategy"""
        for name in (arg.strip().split() or ["matthijs", "alice", "bruce", "sam"]):
            print(f"\n=== {name} ===")
            play(self.port, render(name, self.strategy, self.cfg), self.cfg)
            time.sleep(0.6)

    def do_texts(self, arg: str):
        """texts  — play every phrase in TEST_TEXTS under the current strategy"""
        for text in TEST_TEXTS:
            print(f"\n=== {text!r} ===")
            play(self.port, render(text, self.strategy, self.cfg), self.cfg)
            time.sleep(0.6)

    def do_matrix(self, arg: str):
        """matrix  — play every TEST_TEXTS phrase under every strategy (long!)"""
        for strat in STRATEGIES:
            print(f"\n############ strategy: {strat} ############")
            for text in TEST_TEXTS:
                print(f"  {text!r}")
                play(self.port, STRATEGIES[strat](text, self.cfg), self.cfg)
                time.sleep(0.5)
            time.sleep(1.0)

    def do_compare(self, arg: str):
        """compare STRAT_A STRAT_B TEXT ...  — same text, two strategies"""
        parts = arg.split(maxsplit=2)
        if len(parts) < 3:
            print("usage: compare STRAT_A STRAT_B TEXT")
            return
        a, b, text = parts
        for strat in (a, b):
            if strat not in STRATEGIES:
                print(f"unknown strategy: {strat}")
                return
        for strat in (a, b):
            print(f"\n=== {strat} ===")
            play(self.port, render(text, strat, self.cfg), self.cfg)
            time.sleep(0.8)

    def do_set(self, arg: str):
        """set KEY=VALUE  — override a Config field (see `show` for keys)"""
        try:
            k, v = arg.split('=', 1)
            k, v = k.strip(), v.strip()
            cur = getattr(self.cfg, k)
            if isinstance(cur, bool):
                new = v.lower() in ('1', 'true', 'yes', 'on')
            else:
                new = type(cur)(v)
            self.cfg = replace(self.cfg, **{k: new})
            print(f"{k} = {new}")
        except Exception as e:
            print(f"err: {e}")

    def do_patch(self, arg: str):
        """patch <n>  — GM patch (52=Choir Aahs, 54=Voice Oohs, 85=Charang, ...)"""
        try:
            self.cfg = replace(self.cfg, patch=int(arg))
            print(f"patch = {self.cfg.patch}")
        except Exception:
            print("usage: patch <int>")

    def do_show(self, _):
        """Show current config and active strategy."""
        for k, v in self.cfg.__dict__.items():
            print(f"  {k} = {v}")
        print(f"  strategy = {self.strategy}")

    def do_quit(self, _):
        """Exit the lab."""
        return True

    do_exit = do_quit
    do_EOF = do_quit


def main():
    port = find_port()
    print(f"port: {port}")
    Lab(port).cmdloop()


if __name__ == "__main__":
    main()
