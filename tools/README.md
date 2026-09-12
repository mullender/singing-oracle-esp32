# tools/

Local development tools for the Singing Oracle.

## `sing.py`

Send a hummed melody to the AtomS3 over USB. The device must be flashed with
firmware that runs the MIDI passthrough loop (`Serial.read()` -> `Serial1.write()`)
— that is `firmware/` at `main` on and after commit that adds the passthrough.

### Setup

```sh
pip install pyserial
```

### Use

```sh
python3 tools/sing.py "hello there"
python3 tools/sing.py "matthijs"
python3 tools/sing.py "did the house just sing?"
python3 tools/sing.py "one" --seed 42
python3 tools/sing.py "silent test" --dry-run
python3 tools/sing.py "brass" --program 56   # GM patch 57 = Trumpet
```

The script picks the first `/dev/tty.usbmodem*` or `/dev/ttyACM*` port it
finds. Override with `--port`.

### What it does

- Splits the text into syllables (vowel-cluster count).
- Seeds a random walk from `sha1(text)` so the same input always sounds the
  same. Override with `--seed`.
- Walks in C major, +/-2 scale degrees per syllable, from a hash-picked root.
- Duration 200-400 ms per syllable; final syllable 1.5x.
- Cadence: statements descend on the last note, questions rise.
- Sends General MIDI program change (default Choir Aahs, GM patch 53) then
  note-on / delay / note-off for each note. All on channel 1.

This is a proof-of-concept generator. The final version will live in Home
Assistant and publish note lists over MQTT; the algorithm here is what will
run inside HA.
