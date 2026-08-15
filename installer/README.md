# installer/

The browser flasher for `singing-oracle-esp32`.

## Deployed

Live at **<https://mullender.github.io/singing-oracle-esp32/>**. Open the
page in Chrome or Edge on desktop, plug in an AtomS3 Lite over USB, and
click Install. The page erases the chip and flashes a fresh Singing Oracle
build over Web Serial.

The site is published by `.github/workflows/deploy-installer.yml`. The
workflow builds the vendored esp-web-tools bundle, runs PlatformIO to
build the firmware, and copies the four flash images
(`bootloader.bin`, `partitions.bin`, `boot_app0.bin`, `firmware.bin`)
plus `manifest.json` and the built esp-web-tools bundle into `_site/`
before deploying to GitHub Pages.

## Layout

```
installer/
  index.html          the flasher page
  manifest.json       ESP Web Tools multi-part manifest (committed;
                      edited when the flash layout changes)
  vendor/
    esp-web-tools/    git submodule → mullender/esp-web-tools
```

## Running locally

Serve the repository root on localhost, then open the installer in Chrome
or Edge:

```sh
python3 -m http.server 8765
```

Then open `http://localhost:8765/installer/`.

The installer loads `./vendor/dist/install-button.js`. That file is not
checked in — the deploy workflow builds it. For local serving, build the
vendored fork once and copy the output into `installer/vendor/dist/`:

```sh
cd installer/vendor/esp-web-tools
npm ci
bash script/build
mkdir -p ../dist
cp -r dist/web/. ../dist/
```

## Vendored dependencies

- **`vendor/esp-web-tools/`** — git submodule pointing to
  `mullender/esp-web-tools` on branch `feat/awaited-post-flash-callback`.
  The branch carries only PR 733 (an awaited `onPostFlash` callback) on
  top of upstream `esphome/esp-web-tools` main. The deployed page loads
  only this pinned, same-origin build. It has no CDN fallback.

## What the installer does NOT do

- Post-flash configuration. WiFi and MQTT credential setup is a follow-up
  and will use the awaited `onPostFlash` callback from the vendored fork.
- Persistence of setup data. Any values live in memory for the duration of
  the page session; nothing is sent to any remote service.

## Browser support

Web Serial needs Chrome or Edge on desktop and a secure page. Use HTTPS
or localhost. Safari and Firefox do not support Web Serial and cannot
flash the device from the browser.
