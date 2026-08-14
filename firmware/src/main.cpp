#include <Arduino.h>

// Grove TX on AtomS3 Lite: TXD2 = G1 per m5stack_atoms3/pins_arduino.h
static const int MIDI_TX_PIN = 1;

void setup() {
  Serial1.begin(31250, SERIAL_8N1, -1, MIDI_TX_PIN);
  delay(200);
  static const uint8_t hello[5] = {0xC0, 0x34, 0x90, 0x3C, 0x64};
  Serial1.write(hello, sizeof(hello));
}

void loop() {
}
