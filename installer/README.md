# installer/

The browser flasher for `singing-oracle-esp32`.

Deployed to GitHub Pages by `.github/workflows/deploy-installer.yml` (see
that file after the deploy workflow lands).

## Layout

```
installer/
  index.html          the flasher page
  manifest.json       ESP Web Tools manifest (generated at deploy time)
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

The installer needs the ESP Web Tools bundle at
`installer/vendor/esp-web-tools/dist/web/install-button.js`. That file is
built from the submodule; it is not checked in. Build it once before serving
locally:

```sh
cd installer/vendor/esp-web-tools
npm ci
npm run build
```

## Vendored dependencies

- **`vendor/esp-web-tools/`** — git submodule pointing to
  `mullender/esp-web-tools` on branch `feat/awaited-post-flash-callback`.
  The branch carries only PR 733 (an awaited `onPostFlash` callback) on
  top of upstream `esphome/esp-web-tools` main. The deployed page loads
  only this pinned, same-origin build. It has no CDN fallback.

## What the installer does NOT do

- Firmware distribution. `builds: []` in `manifest.json` is a placeholder.
  Real builds land through the deploy workflow.
- Post-flash configuration. WiFi and MQTT credential setup is a follow-up
  and will use the awaited `onPostFlash` callback from the vendored fork.
- Persistence of setup data. Any values live in memory for the duration of
  the page session; nothing is sent to any remote service.

## Browser support

Web Serial needs Chrome or Edge on desktop and a secure page. Use HTTPS
or localhost. Safari and Firefox do not support Web Serial and cannot
flash the device from the browser.
