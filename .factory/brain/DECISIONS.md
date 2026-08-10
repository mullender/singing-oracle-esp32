# Decisions

## 2026-08-09

- **Mode: Builder mode (fun/whimsy).** The project is explicitly a hobby build,
  not a startup. Skip startup-flavored analysis; optimize for delight and
  demo-ability.
- **Repo name: `singing-oracle-esp32`.** Follows the `<product>-<chip>` pattern
  from `aliro-doorlock-esp32` and `HomeKey-ESP32`. Rejected `synth-esp32`
  because it names the component (M5 Unit Synth) not the product (a
  Home-Assistant-driven singing house), and is collision-prone on GitHub.
- **Dedicated AtomS3 Lite for the synth.** The existing doorkey AtomS3 uses
  I²C for Unit NFC; the Unit Synth is UART. Sharing the Grove port would
  require software serial and complicate working doorkey firmware. A second
  controller keeps concerns separate and lets the synth be a
  network-callable service.
- **HA-brain, synth-dumb architecture.** Home Assistant generates the note
  sequence; the synth controller just plays what it receives over MQTT.
  Melody logic lives where iteration is cheapest (Python + YAML), not on
  the ESP32. Rejected all-on-device (harder to iterate melodies) and full
  multi-voice orchestration (deferred to v2).
- **Distribution via ESP Web Tools installer page on GitHub Pages.** Anyone
  should be able to flash a fresh AtomS3 Lite from Chrome without touching
  PlatformIO or a terminal. Pattern lifted from `aliro-doorlock-esp32/`.
  This is Step 0 — build the pipeline BEFORE writing firmware.
- **First voice: Choir Aahs (GM patch 53) only.** Layering Voice Oohs drone
  and multi-channel orchestration is deferred to v2.
