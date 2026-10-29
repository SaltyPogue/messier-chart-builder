# SaltyPogue Chart Builders

**Created by SaltyPogue** · [www.saltypogue.com](https://www.saltypogue.com) · [Instagram](https://www.instagram.com/saltypogue) · [Facebook](https://www.facebook.com/saltypogue) · [X](https://x.com/saltypogue)

Build a chart of a whole deep-sky catalog from your own astrophotos. Drag your photos onto the grid and the chart updates and saves itself after every photo.

| App | Catalog |
|---|---|
| **Messier Chart Builder** | The 110 Messier objects (M1–M110) |
| **Caldwell Chart Builder** | The 109 Caldwell objects (C1–C109) |
| **Sharpless Chart Builder** | The 313 Sharpless nebulae (Sh2-1 to Sh2-313) |
| **Herschel Chart Builder** | The 400 Herschel objects (the Astronomical League's Herschel 400 list) |
| **Barnard Chart Builder** | Barnard's dark nebulae (B1–B175 and B201–B370) |
| **Abell Chart Builder** | The 86 Abell planetary nebulae (Abell 1–86) |
| **vdB Chart Builder** | The 158 van den Bergh reflection nebulae (vdB 1–158) |

## Download

👉 **[All downloads (latest version)](../../releases/latest)**

| App | Windows | Mac (Apple chip) | Mac (Intel) |
|---|---|---|---|
| **Messier** | [Messier-Chart-Builder.exe](../../releases/latest/download/Messier-Chart-Builder.exe) | [apple-silicon.zip](../../releases/latest/download/Messier-Chart-Builder-Mac-Apple-Silicon.zip) | [intel.zip](../../releases/latest/download/Messier-Chart-Builder-Mac-Intel.zip) |
| **Caldwell** | [Caldwell-Chart-Builder.exe](../../releases/latest/download/Caldwell-Chart-Builder.exe) | [apple-silicon.zip](../../releases/latest/download/Caldwell-Chart-Builder-Mac-Apple-Silicon.zip) | [intel.zip](../../releases/latest/download/Caldwell-Chart-Builder-Mac-Intel.zip) |
| **Sharpless** | [Sharpless-Chart-Builder.exe](../../releases/latest/download/Sharpless-Chart-Builder.exe) | [apple-silicon.zip](../../releases/latest/download/Sharpless-Chart-Builder-Mac-Apple-Silicon.zip) | [intel.zip](../../releases/latest/download/Sharpless-Chart-Builder-Mac-Intel.zip) |
| **Herschel** | [Herschel-Chart-Builder.exe](../../releases/latest/download/Herschel-Chart-Builder.exe) | [apple-silicon.zip](../../releases/latest/download/Herschel-Chart-Builder-Mac-Apple-Silicon.zip) | [intel.zip](../../releases/latest/download/Herschel-Chart-Builder-Mac-Intel.zip) |
| **Barnard** | [Barnard-Chart-Builder.exe](../../releases/latest/download/Barnard-Chart-Builder.exe) | [apple-silicon.zip](../../releases/latest/download/Barnard-Chart-Builder-Mac-Apple-Silicon.zip) | [intel.zip](../../releases/latest/download/Barnard-Chart-Builder-Mac-Intel.zip) |
| **Abell** | [Abell-Chart-Builder.exe](../../releases/latest/download/Abell-Chart-Builder.exe) | [apple-silicon.zip](../../releases/latest/download/Abell-Chart-Builder-Mac-Apple-Silicon.zip) | [intel.zip](../../releases/latest/download/Abell-Chart-Builder-Mac-Intel.zip) |
| **vdB** | [vdB-Chart-Builder.exe](../../releases/latest/download/vdB-Chart-Builder.exe) | [apple-silicon.zip](../../releases/latest/download/vdB-Chart-Builder-Mac-Apple-Silicon.zip) | [intel.zip](../../releases/latest/download/vdB-Chart-Builder-Mac-Intel.zip) |

### Windows

Download the `.exe` and double-click it. Windows may show "Windows protected your PC", because the app isn't from the Microsoft Store: click **More info**, then **Run anyway**.

### Mac

- **Apple chip (M1, M2, M3, M4…)**, most Macs from late 2020 on: the `Mac-Apple-Silicon` file
- **Intel Mac**: the `Mac-Intel` file

Not sure which you have? Apple menu  → **About This Mac** → look at **Chip** or **Processor**.

1. Double-click the downloaded zip, then drag the app into your **Applications** folder.
2. Open it. macOS will say it can't verify the app, because it isn't from the App Store. Click **Done**.
3. Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to the app's name.

You only need to do this once per app.

## Using the apps (Version 1.2)

The first time an app opens, a short welcome guide explains the basics. You can open it again any time with **Help**.

- **Drag photos onto the window.** Files named with their catalog number *or the object's name* go to the right square automatically. You can drop many at once, or a whole folder, and a progress bar shows how it's going (with Cancel).
  - Messier: `M31.jpg`, `Messier 81.png`, `Andromeda Galaxy.jpg`, or the NGC number such as `NGC 224.jpg`
  - Caldwell: `C20.jpg`, `Caldwell 49.tif`, the NGC/IC number such as `NGC 7000.jpg`, or a name such as `Bubble Nebula.jpg`
  - Sharpless: `Sh2-155.jpg`, `Sharpless 155.png`, a matching NGC/IC/Messier number such as `IC 1805.jpg`, or a name such as `Heart Nebula.jpg`
  - Herschel: `NGC 891.jpg`, `ngc7814.png`, or the Messier/Caldwell number of a list object such as `M33.jpg` or `C23.jpg`
  - Barnard: `B33.jpg`, `Barnard 72.png`, or a well-known name such as `Horsehead.jpg`
  - Abell: `Abell 21.jpg`, `A39.png`, `PN A66 31.tif`, or another designation such as `NGC 6742.jpg`
  - vdB: `vdB 139.jpg`, `vdb142.png`, another designation such as `NGC 7023.jpg` or `IC 2118.jpg`, or a name such as `Iris.jpg`
- **Any photo format you're likely to have:** JPG, PNG, WebP, and 8-, 16- and 32-bit TIFFs straight from Siril, PixInsight, APP or DeepSkyStacker. A stack that hasn't been stretched yet (it looks almost black) is brightened automatically for the chart. Your file isn't changed.
- **Click** a square to pick a photo for it. **Right-click** (or Control-click on a Mac) for more:
  - **Adjust framing…**: drag the box to move it and scroll (or use the slider) to zoom. **Show whole photo** fits big targets like M31 without cutting off the ends; zoom in to fill the square with small targets like M57.
  - **Add log / notes…**: record your dates, total exposure, sub length and count, gain, equipment and your own notes. Each log is saved as a plain text file next to that photo (for example `M31_log.txt`), and a one-line summary shows in the hover preview.
  - **Open original** or **Remove photo**.
- **Undo** (or Ctrl+Z / Cmd+Z) puts back a photo you removed, replaced or changed the framing of, or everything after **Clear all**.
- **Missing list** shows what's still to photograph. Click an object to find it on the chart, double-click to choose a photo for it, and **Save checklist…** as a text file or a spreadsheet (CSV).
- **Rest the mouse on a photo** to see a larger preview.
- **Export chart…** saves a PNG, JPG or TIFF. Each chart is also saved automatically in its own folder in your home folder (`Messier Chart`, `Caldwell Chart`, `Sharpless Chart`, `Herschel Chart`, `Barnard Chart`, `Abell Chart`, `vdB Chart`).
- **Edit title…**, **Library folder**, **Clear all…** and **Star border: On/Off** are in the toolbar.

Your original photos are never changed. The apps work from copies.

## How the code is organised

All seven apps share one engine, so a fix or new feature is made once and every app gets it.

| File | What it is |
|---|---|
| `chart_core.py` | The whole app: window, chart, framing, logs, undo, missing list… shared by all seven |
| `catalogs/<name>.py` | One small file per catalog: object names, grid size, description and file-name matching |
| `<name>_chart.py` | Three-line start file for each app (picks its catalog) |
| `assets/` | Footer icons for each app |
| `*_icon.ico` / `*_icon.icns` | Windows and Mac app icons |
| `website/` | Website pages and the download counter snippet |
| `VERSION` | The version number for the downloads. Keep it the same as `APP_VERSION` in `chart_core.py` |

Every change pushed to GitHub builds all 21 downloads (7 apps × Windows, Mac Apple chip and Mac Intel), checks that each one starts, and publishes them to the release for the current version. The download links never change.
