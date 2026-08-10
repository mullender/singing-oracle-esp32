# Current state

The factory is starting a brand-new project: **Singing Oracle** — an ESP32
bridge that plays synthesized "singing" melodies (Choir Aahs, GM patch 53) on
an M5 Unit Synth in response to Home Assistant events. Origin story in
`DESIGN.md` at the repo root.

- **No code yet.** Repo has only `README.md` and `DESIGN.md`. Design is APPROVED.
- **First real task is Step 0 (Distribution Plan):** scaffold `firmware/`
  (PlatformIO, target `m5stack-atoms3`), `installer/` (ESP Web Tools embed),
  `installer/vendor/esp-web-tools` (git submodule), `artifacts/`, and
  `.github/workflows/deploy-installer.yml`. Verify the empty installer page
  loads on GH Pages and Web Serial detects a plugged AtomS3 — BEFORE writing
  any firmware.
- **Reference project to mirror:** `~/Development/aliro-doorlock-esp32/`.
  Especially: `installer/index.html`, `installer/README.md`, `installer/js/*`
  (keep serial-monitor + setup-flow + install-controller; skip
  matter-payload/qr-render/device-protocol which are Matter-specific), the
  vendored `installer/vendor/esp-web-tools` submodule, and
  `.github/workflows/deploy-installer.yml`.
- **GitHub repo:** `mullender/singing-oracle-esp32` (created out-of-band by
  the user in parallel with factory init; treat as existing).
- **Only Lead can push.** Builder and Reviewer hand off commits and never push.

## Suggested first Builder assignment

Scaffold `firmware/` as an empty PlatformIO project targeting
`m5stack-atomsupled` (verify exact `board = ` string for AtomS3 Lite in the
PlatformIO board index — could be `m5stack-atoms3` too), and commit. Nothing
functional yet. Just the structure. Small, bounded, easy to review.

Do NOT scaffold the installer yet in that same task. Split installer scaffolding
into its own follow-up. Each Builder task small.
