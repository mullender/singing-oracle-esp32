#include <Arduino.h>

// Grove TX to Unit Synth: G2 (bench-verified; TXD2 label in variant is misleading for this pairing)
static const int MIDI_TX_PIN = 2;

void setup() {
  Serial.begin(115200);                                 // USB CDC in from host
  Serial1.begin(31250, SERIAL_8N1, -1, MIDI_TX_PIN);    // MIDI out to Unit Synth
  delay(200);                                           // let SAM2695 finish booting

  // Boot beep so a fresh flash is audibly identifiable.
  static const uint8_t note_on[]  = {0xC0, 0x34, 0x90, 0x3C, 0x64};
  static const uint8_t note_off[] = {0x80, 0x3C, 0x00};
  Serial1.write(note_on, sizeof(note_on));
  delay(800);
  Serial1.write(note_off, sizeof(note_off));
}

void loop() {
  // MIDI passthrough: any bytes the host sends over USB CDC go straight to the synth.
  while (Serial.available()) {
    Serial1.write(Serial.read());
  }
}
