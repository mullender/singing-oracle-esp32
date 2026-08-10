# singing-oracle-esp32

A house that **hums** at you.

The Singing Oracle is a small ESP32 project that turns an
[M5 Unit Synth (SAM2695)](https://shop.m5stack.com/products/midi-synthesizer-unit-sam2695)
into a musical voice for [Home Assistant](https://www.home-assistant.io/). Door
events, notifications, weather, and any other HA state change trigger short
melodies played on GM patch 53 (Choir Aahs) — pitched phrases that feel like
wordless singing.

Each family member gets a distinct leitmotif when they tap the door with their
Aliro NFC key. Guests get to smile and ask "wait, did the house just *sing*?"

## Status

Pre-scaffold. See [`DESIGN.md`](DESIGN.md) for the full design doc — problem
statement, approaches considered, chosen architecture, distribution plan, and
next steps. Step 0 is scaffolding the firmware repo and the ESP Web Tools
installer page (Chrome-only flash-from-URL), mirroring the layout of
[`aliro-doorlock-esp32`](https://github.com/mullender/aliro-doorlock-esp32).

## Hardware

- M5Stack AtomS3 Lite (dedicated to this device; not shared with a doorkey)
- M5 Unit Synth (SAM2695), UART/MIDI at 31250 baud
- Small amplified speaker or line-in to existing home audio
- Home Assistant running an MQTT broker on the local network

## License

TBD.
