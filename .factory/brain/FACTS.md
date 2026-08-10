# Facts

## Hardware
- **M5 Unit Synth** = SAM2695. Interface is **UART / serial MIDI at 31250
  baud** — NOT I²C. Confirmed via M5Stack product page. This is why the
  project uses a dedicated AtomS3 Lite instead of sharing the existing
  doorkey AtomS3 (which is I²C-only via its Grove port with the Unit NFC).
- **Controller:** dedicated M5 AtomS3 Lite. Grove UART pins carry MIDI to the
  Unit Synth. Do not share the doorkey AtomS3.
- **Doorkey system (already working, do NOT touch):** Aliro on a separate
  AtomS3 with Unit NFC over I²C. Lives at
  `~/Development/aliro-doorlock-esp32/`.
- **Audio out:** Unit Synth has line-out. Speaker choice deferred (open
  question in DESIGN.md).
- **HA integration:** MQTT broker on the local Home Assistant instance.

## Software
- **MIDI over UART:** 31250 baud, 8-N-1. Bytes are raw MIDI (`0xC0 <patch>`
  for program change, `0x90 <note> <vel>` for note on, `0x80 <note> 0x00`
  for note off).
- **GM patch 53 = Choir Aahs** — the primary voice for the Singing Oracle.
  MIDI program-change value is 52 (0-indexed) = `0xC0 0x34`.
- **Chosen architecture:** HA-brain, synth-dumb. Home Assistant generates
  the melody (Python is better at syllable counting, per-person theming, and
  mood logic). Synth controller subscribes to MQTT, receives a JSON note
  list, sequences notes with timing. Firmware stays simple and rarely needs
  reflashing after v0.1.
- **Distribution:** ESP Web Tools installer page served from GitHub Pages.
  Users flash from Chrome by URL. Pattern lifted from Aliro's
  `installer/` + `.github/workflows/deploy-installer.yml`.
