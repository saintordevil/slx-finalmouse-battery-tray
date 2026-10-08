# Changelog

## 2026-10-08: Initial SLX version

### What changed

- Created a separate Starlight X project from the HID-only [ULX tray](https://github.com/saintordevil/ulx-finalmouse-battery-tray), with matching installer and README structure.
- Selected the verified SLX receiver `361D:0300` and wired mouse `361D:0310`, vendor usage `FF00/1`, interface `1`. ULX and pointer/keyboard interfaces are excluded.
- Used SLX report IDs `1`/`2` and its reported state of charge. Wireless reads query link, charging, and battery status; wired reads query charging and battery status directly.
- Showed a live white percentage during charging, with charging status and session details on hover. A bounded 180 ms number transition and a 1.2-second grey-to-white number pulse replace the bolt. The pulse keeps its phase across percentage changes. Eight cached native icon handles avoid rebuilding icon files on every pulse frame. Windows reduced-motion preference is respected.
- Added a Charge details submenu for full history, kept native tooltips within 127 characters, and made unavailable readings visibly unknown.
- Kept SLX history and instance locks separate from ULX. The original ULX history remains compatible with its renamed project.
- Replaced the inherited previews with actual SLX charging and wireless tray screenshots.

### Validation

- All **103 tests passed** from the installed project-local environment. They cover SLX captures, live wired and wireless charging, invalid states, bounded timeouts, exact device selection, pulse continuity across percentage changes, animation cancellation, reduced motion, bounded native icon caching, tooltip length, history, and Windows launcher/stop behavior.
- Physical checks on Windows 11 identified StarlightX Dongle and StarlightX Mouse. Read-only captures included wireless 42% at 3,844 mV and wired 55% at 4,192 mV with the charging flag set. The live installed tray subsequently tracked charging from 70% through higher percentages.
- Wireless reconnection was physically verified at 96%, with the completed 85%-to-99% session retained across restarts. Radio inactivity retains the last percentage with an idle label. A deterministic startup-race regression verifies that the initial placeholder cannot be cached as a later reading.
- The public Xpanel application supplied the protocol reference. No mouse settings, pairing, or firmware were changed.

### Measured impact

The installed scheduled-start app was observed for 74.3 seconds on Windows 11 with Python 3.11.9, Pillow 12.3.0, pystray 0.19.5, hidapi 0.15.0, and six 1.17.0. The charging pulse ran in the existing poll thread. No browser or additional animation worker ran.

| Observation | Resident working set | Private committed memory |
|---|---:|---:|
| End of warm charging observation, full Python process tree | 39.68 MiB | 23.34 MiB |
| Sampled maximum | 41.86 MiB | 25.49 MiB |

Charging CPU was approximately **0.020% of the 24-logical-processor machine**, from 0.297 process CPU-seconds over 62.1 seconds. The observation includes the tray interpreter and its environment redirector. It excludes the measurement helper. Handles remained bounded. Sampling can miss brief startup helpers and peaks; these figures are observations on one PC, not guaranteed ceilings. Summed working sets may count shared pages twice, and private commit is not resident RAM.

Other SLX USB IDs, all firmware combinations, and a second PC have not been verified. Wired status failure preserves USB presence but cannot supply a fresh battery percentage. Charge-history duration can include unavailable intervals before the next valid noncharging reading.
