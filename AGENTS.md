# SLX Finalmouse Battery Tray

- Preserve native HID, the existing tray UI, saved charge history, and lightweight local launcher. Keep the runtime and published package HID-only.
- Select the exact model's vendor HID interface; never query pointer or keyboard interfaces. Keep ULX and SLX state, mutexes, and stop targets separate.
- Display fresh SLX state of charge as a number, solid white on wireless and pulsing grey-to-white while the device reports charging. Use the reported charging flag, never infer charging from cable presence. Radio inactivity retains the last known number with an idle label; missing-device and failed reads show `--`. Both preserve pending history. A fresh wired or wireless noncharging percentage closes a session. Keep number transitions short and preserve the charge-pulse phase across percentage changes. Keep native icon caches bounded, serialize icon assignment and visibility with handle creation, avoid per-frame disk work, and respect Windows animation settings.
- For device or charge-state changes, verify real hardware where available plus disconnect recovery and saved state. Use disposable fixtures for offline tests. For lifecycle changes, include the Python environment redirector and temporary startup helper in full-tree resource checks.

SLX uses `%LOCALAPPDATA%\slx-finalmouse-battery-tray` and `Local\SlxFinalmouseBatteryTray`. Verified devices are receiver `361D:0300` and wired mouse `361D:0310`, both vendor interface 1. Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for SLX report IDs and state-of-charge decoding before protocol edits.
