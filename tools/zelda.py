#!/usr/bin/env python3
"""Play Zelda ocarina and theme motifs on the Singing Oracle.

Requires the passthrough firmware and pyserial.

    python3 tools/zelda.py list
    python3 tools/zelda.py lullaby
    python3 tools/zelda.py chill              # atmospheric playlist
    python3 tools/zelda.py chill --loop
    python3 tools/zelda.py song_of_storms --patch 89   # Fantasia pad

Melodies are approximate hand-transcriptions from memory of the well-known
motifs — a purist should feel free to fix pitches, tempo, or add second
voices. The passthrough firmware happily accepts polyphony (chord tuples).
"""

import argparse
import glob
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial required: pip install pyserial")

ATOMS3_VID, ATOMS3_PID = 0x303A, 0x1001

# GM patches worth trying for a chill Zelda vibe:
#   52 Choir Aahs, 54 Voice Oohs, 89 Fantasia, 92 Bowed Glass, 94 Halo Pad,
#   46 Orchestral Harp, 68 Oboe, 74 Flute, 79 Ocarina (yes, GM has it), 106 Shamisen.
CHOIR_AAHS = 52
OCARINA = 79

# MIDI notes by name, C4 = middle C = 60.
_ROOTS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def n(name: str) -> int:
    """'C4' -> 60, 'F#5' -> 78, 'Bb3' -> 58."""
    if len(name) == 2:
        letter, octave = name[0], int(name[1])
        acc = 0
    else:
        letter, acc_ch, octave = name[0], name[1], int(name[2:])
        acc = {'#': 1, 'b': -1}[acc_ch]
    return 12 * (octave + 1) + _ROOTS[letter] + acc


# ---------------------------------------------------------------- tunes --
# Each tune: dict with 'patch' (GM instrument, 0-indexed), 'bpm' hint, and
# 'notes' as a list of (pitch_or_chord_or_None, beats) tuples. None is a rest.
# `beats` is in quarter-notes for legibility; multiply by 60000/bpm at play.

TUNES = {
    # Zelda's Lullaby — 3/4, dreamy 6-note motif. Approximate.
    'lullaby': {
        'patch': CHOIR_AAHS, 'bpm': 90,
        'notes': [
            (n('B4'), 2), (n('D5'), 1), (n('A4'), 2),
            (n('G4'), 2), (n('E4'), 1), (n('D5'), 2),
            (n('B4'), 2), (n('D5'), 1), (n('A4'), 2),
            (n('E4'), 4),
            (None, 1),
            (n('B4'), 2), (n('D5'), 1), (n('A4'), 2),
            (n('G4'), 2), (n('E4'), 1), (n('D5'), 2),
            (n('B4'), 2), (n('D5'), 1), (n('A4'), 2),
            (n('D4'), 4),
        ],
    },

    # Song of Time — solemn ascending pattern.
    'song_of_time': {
        'patch': CHOIR_AAHS, 'bpm': 80,
        'notes': [
            (n('A4'), 1), (n('D5'), 1), (n('F5'), 2),
            (n('A4'), 1), (n('D5'), 1), (n('F5'), 2),
            (n('E5'), 1), (n('F5'), 1), (n('E5'), 1), (n('C5'), 1),
            (n('A4'), 4),
        ],
    },

    # Song of Storms — driving triplets. Not chill, but iconic.
    'song_of_storms': {
        'patch': OCARINA, 'bpm': 140,
        'notes': [
            (n('D5'), 1), (n('F5'), 1), (n('D6'), 2),
            (n('D5'), 1), (n('F5'), 1), (n('D6'), 2),
            (n('E6'), 1), (n('F6'), 1), (n('E6'), 1), (n('F6'), 1),
            (n('E6'), 1), (n('C6'), 1), (n('A5'), 2),
            (n('A5'), 1), (n('D5'), 1), (n('F5'), 1), (n('G5'), 1),
            (n('A5'), 4),
        ],
    },

    # Saria's Song — bouncy, playful.
    'sarias_song': {
        'patch': OCARINA, 'bpm': 120,
        'notes': [
            (n('F5'), 1), (n('A5'), 1), (n('B5'), 2),
            (n('F5'), 1), (n('A5'), 1), (n('B5'), 2),
            (n('F5'), 1), (n('A5'), 1), (n('B5'), 1), (n('E6'), 1),
            (n('D6'), 1), (n('B5'), 1), (n('C6'), 2),
            (n('E5'), 1), (n('C6'), 1), (n('B5'), 2),
        ],
    },

    # Epona's Song — three-note pastoral motif.
    'eponas_song': {
        'patch': OCARINA, 'bpm': 100,
        'notes': [
            (n('D5'), 2), (n('B4'), 2), (n('A4'), 4),
            (n('D5'), 2), (n('B4'), 2), (n('A4'), 4),
            (n('D5'), 1), (n('B4'), 1), (n('A4'), 1), (n('B4'), 1),
            (n('D5'), 4),
        ],
    },

    # Sun's Song — hymn-like, ascending resolution.
    'suns_song': {
        'patch': CHOIR_AAHS, 'bpm': 90,
        'notes': [
            (n('A4'), 1), (n('F5'), 1), (n('D5'), 2),
            (n('A4'), 1), (n('F5'), 1), (n('D5'), 2),
            (n('E5'), 1), (n('C5'), 1), (n('A4'), 1), (n('F4'), 1),
            (n('D4'), 4),
        ],
    },

    # Great Fairy Fountain — melancholic arpeggio. Approximate.
    'great_fairy': {
        'patch': 46, 'bpm': 78,  # Orchestral Harp
        'notes': [
            (n('D5'), 1), (n('F5'), 1), (n('A5'), 1), (n('D6'), 1),
            (n('C6'), 1), (n('A5'), 1), (n('F5'), 1), (n('D5'), 1),
            (n('E5'), 1), (n('G5'), 1), (n('B5'), 1), (n('E6'), 1),
            (n('D6'), 1), (n('B5'), 1), (n('G5'), 1), (n('E5'), 1),
        ],
    },

    # Kokiri Forest opening motif.
    'kokiri': {
        'patch': OCARINA, 'bpm': 108,
        'notes': [
            (n('E5'), 1), (n('G5'), 1), (n('A5'), 1), (n('B5'), 2), (n('A5'), 1),
            (n('G5'), 1), (n('E5'), 1), (n('D5'), 1), (n('E5'), 3),
            (None, 1),
            (n('E5'), 1), (n('G5'), 1), (n('A5'), 1), (n('B5'), 2), (n('C6'), 1),
            (n('B5'), 1), (n('A5'), 1), (n('G5'), 1), (n('A5'), 4),
        ],
    },

    # Zelda's Theme — main overworld hook, well-known.
    'zelda_theme': {
        'patch': OCARINA, 'bpm': 96,
        'notes': [
            (n('B4'), 4),
            (n('D5'), 2), (n('A4'), 6),
            (n('G4'), 2), (n('A4'), 2), (n('B4'), 2), (n('D5'), 2),
            (n('A4'), 8),
            (n('B4'), 2), (n('D5'), 2), (n('A5'), 4),
            (n('G5'), 2), (n('D5'), 2), (n('B4'), 2), (n('A4'), 2),
            (n('G4'), 8),
        ],
    },
}

# The "chill" playlist — atmospheric, in reflective order.
CHILL = ['lullaby', 'great_fairy', 'song_of_time', 'suns_song',
         'kokiri', 'eponas_song', 'sarias_song', 'zelda_theme']


# --------------------------------------------------------------- port --

def find_port() -> str:
    for p in list_ports.comports():
        if p.vid == ATOMS3_VID and p.pid == ATOMS3_PID:
            return p.device
    fallback = sorted(glob.glob("/dev/tty.usbmodem*") + glob.glob("/dev/ttyACM*"))
    if fallback:
        print(f"AtomS3 by VID:PID not found; falling back to {fallback[0]}", file=sys.stderr)
        return fallback[0]
    sys.exit("no serial ports found — is the AtomS3 plugged in?")


# ------------------------------------------------------------ playback --

def play_tune(port: str, tune: dict, patch_override: int | None = None,
              velocity: int = 100, gap_ms: int = 15) -> None:
    beat_ms = 60_000 / tune['bpm']
    patch = patch_override if patch_override is not None else tune['patch']
    with serial.Serial(port, 115200, timeout=1) as s:
        s.dtr = False
        s.rts = False
        time.sleep(0.1)
        s.write(bytes([0xC0, patch]))
        time.sleep(0.05)
        for pitch, beats in tune['notes']:
            dur = beats * beat_ms / 1000
            if pitch is None:
                time.sleep(dur)
                continue
            pitches = pitch if isinstance(pitch, (list, tuple)) else [pitch]
            for m in pitches:
                s.write(bytes([0x90, m, velocity]))
            time.sleep(dur)
            for m in pitches:
                s.write(bytes([0x80, m, 0]))
            time.sleep(gap_ms / 1000)


# ----------------------------------------------------------------- CLI --

def main() -> None:
    ap = argparse.ArgumentParser(description="Zelda tunes on the Singing Oracle.")
    ap.add_argument("tune", nargs="?", help="Tune name, 'chill', or 'list'")
    ap.add_argument("--port", help="Serial port (default: auto-detect AtomS3)")
    ap.add_argument("--patch", type=int, help="GM patch override (0-indexed)")
    ap.add_argument("--loop", action="store_true", help="Loop the tune/playlist forever")
    ap.add_argument("--gap", type=int, default=800, help="ms between tunes in playlist (default 800)")
    args = ap.parse_args()

    if not args.tune or args.tune == "list":
        for name, tune in TUNES.items():
            marker = "*" if name in CHILL else " "
            print(f"  {marker} {name:16s}  bpm={tune['bpm']:3d}  patch={tune['patch']}")
        print("\n  * = in the 'chill' playlist. `python3 tools/zelda.py chill` plays them all.")
        return

    port = args.port or find_port()

    if args.tune == "chill":
        playlist = CHILL
    elif args.tune in TUNES:
        playlist = [args.tune]
    else:
        sys.exit(f"unknown tune: {args.tune}. Try 'list'.")

    def run_once():
        for name in playlist:
            print(f"~ {name}")
            play_tune(port, TUNES[name], patch_override=args.patch)
            time.sleep(args.gap / 1000)

    try:
        while True:
            run_once()
            if not args.loop:
                break
    except KeyboardInterrupt:
        print("\nfading out.")


if __name__ == "__main__":
    main()
