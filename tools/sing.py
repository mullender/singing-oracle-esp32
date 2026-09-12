#!/usr/bin/env python3
"""Send a hummed melody to the Singing Oracle via USB MIDI passthrough.

Requires pyserial: pip install pyserial

Usage:
    python3 tools/sing.py "hello there"
    python3 tools/sing.py "matthijs" --port /dev/tty.usbmodem1101
    python3 tools/sing.py "did the house just sing?" --dry-run
"""

import argparse
import hashlib
import random
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial required: pip install pyserial")

# C major, C4..C5. Melody stays here so it always sounds tonal.
C_MAJOR = [60, 62, 64, 65, 67, 69, 71, 72]

CHOIR_AAHS = 0x34  # GM patch 53, 0-indexed

# Espressif USB-JTAG/serial device on the AtomS3 (S3 native USB CDC).
ATOMS3_VID = 0x303A
ATOMS3_PID = 0x1001


def find_port() -> str:
    ports = list(list_ports.comports())
    atoms3 = [p.device for p in ports if p.vid == ATOMS3_VID and p.pid == ATOMS3_PID]
    if atoms3:
        if len(atoms3) > 1:
            print(f"multiple AtomS3 ports found; using {atoms3[0]}", file=sys.stderr)
        return atoms3[0]
    if not ports:
        sys.exit("no serial ports found — is the AtomS3 plugged in?")
    listing = "\n  ".join(f"{p.device}  VID:PID={p.vid:04X}:{p.pid:04X}  {p.description}"
                          for p in ports if p.vid is not None)
    sys.exit(f"no AtomS3 (VID:PID={ATOMS3_VID:04X}:{ATOMS3_PID:04X}) found. "
             f"Ports seen:\n  {listing}\nUse --port to override.")


def syllable_count(word: str) -> int:
    """Count vowel clusters. Rough but dependency-free."""
    vowels = set("aeiouyAEIOUY")
    count, in_vowel = 0, False
    for c in word:
        if c in vowels:
            if not in_vowel:
                count += 1
                in_vowel = True
        else:
            in_vowel = False
    return max(count, 1)


def generate_melody(text: str, seed: int | None = None) -> list[tuple[int, int]]:
    """Turn text into (note, duration_ms) pairs.

    Approach B from DESIGN.md: root from hash(text), scale-degree random walk,
    ~200-400ms per syllable, final syllable longer, cadence rule on last note.
    """
    words = text.split() or [text]
    total_syllables = sum(syllable_count(w) for w in words)

    if seed is None:
        seed = int(hashlib.sha1(text.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    # Root scale degree.
    idx = rng.randint(0, len(C_MAJOR) - 1)

    notes: list[tuple[int, int]] = []
    for i in range(total_syllables):
        step = rng.randint(-2, 2)
        idx = max(0, min(len(C_MAJOR) - 1, idx + step))
        duration = rng.randint(200, 400)
        if i == total_syllables - 1:
            duration = int(duration * 1.5)  # final syllable lingers
        notes.append((C_MAJOR[idx], duration))

    # Cadence: statements descend, questions rise.
    if len(notes) >= 2:
        is_question = text.rstrip().endswith("?")
        last_note, last_dur = notes[-1]
        prev_note = notes[-2][0]
        if is_question and last_note <= prev_note:
            notes[-1] = (min(C_MAJOR[-1], last_note + 2), last_dur)
        elif not is_question and last_note >= prev_note:
            notes[-1] = (max(C_MAJOR[0], last_note - 2), last_dur)

    return notes


def play(port: str, notes: list[tuple[int, int]], program: int = CHOIR_AAHS, velocity: int = 100) -> None:
    """Send program change + note-on/note-off sequence over MIDI-over-USB."""
    with serial.Serial(port, 115200, timeout=1) as s:
        # ESP32-S3 native USB CDC does not use DTR/RTS for reset, but some
        # drivers pulse them on open — hold them low so the chip does not glitch.
        s.dtr = False
        s.rts = False
        time.sleep(0.1)  # let the CDC endpoint settle before writing
        s.write(bytes([0xC0, program]))
        time.sleep(0.05)
        for note, dur_ms in notes:
            s.write(bytes([0x90, note, velocity]))
            time.sleep(dur_ms / 1000)
            s.write(bytes([0x80, note, 0x00]))
            time.sleep(0.02)


def main() -> None:
    ap = argparse.ArgumentParser(description="Send a hummed melody to the Singing Oracle.")
    ap.add_argument("text", help="Text to turn into a melody.")
    ap.add_argument("--port", help="Serial port (default: auto-detect /dev/tty.usbmodem*)")
    ap.add_argument("--seed", type=int, help="Random seed (default: hash of text)")
    ap.add_argument("--program", type=int, default=CHOIR_AAHS,
                    help=f"GM patch (0-indexed; default {CHOIR_AAHS} = Choir Aahs)")
    ap.add_argument("--dry-run", action="store_true", help="Print the note list; do not open the port.")
    args = ap.parse_args()

    notes = generate_melody(args.text, seed=args.seed)
    for i, (n, d) in enumerate(notes):
        print(f"  {i:2d}: note={n:3d}  dur={d:3d}ms", file=sys.stderr)

    if args.dry_run:
        return

    port = args.port or find_port()
    print(f"playing on {port}", file=sys.stderr)
    play(port, notes, program=args.program)


if __name__ == "__main__":
    main()
