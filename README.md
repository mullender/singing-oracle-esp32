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

Firmware scaffolded. On boot the AtomS3 Lite sends one Choir Aahs middle-C
to the Unit Synth over UART. The browser installer is live at
<https://mullender.github.io/singing-oracle-esp32/>. See
[`DESIGN.md`](DESIGN.md) for the roadmap — MQTT-driven note lists, HA
melody generation, and per-person themes are next.

## Hardware

- M5Stack AtomS3 Lite (dedicated to this device; not shared with a doorkey)
- M5 Unit Synth (SAM2695), UART/MIDI at 31250 baud
- Small amplified speaker or line-in to existing home audio
- Home Assistant running an MQTT broker on the local network

## License

TBD.
