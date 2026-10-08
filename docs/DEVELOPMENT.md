# Development and tests

Install the project first. Run these commands in Command Prompt, replacing the example path with your checkout location.

The full regression suite uses the same native dependencies as the application:

```bat
cd /d "C:\Users\User\Desktop\Programs\slx-finalmouse-battery-tray"
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" -B -m unittest discover -v
```

Tests use fake HID responses and isolated application state. Windows launcher and cleanup tests start temporary recorder/helper processes. They do not start the real tray or query live hardware. Physical battery, cable-switch, disconnect, and history checks are separate. See [release validation](../CHANGELOG.md).

## Reader behavior

`native_hid.py` selects only vendor `361D`, usage page `FF00`, usage `1`, interface `1`. The supported receiver is `0300`; the wired mouse is `0310`. ULX, pointer, keyboard, and duplicate matching interfaces are rejected.

SLX uses output report ID `1`, input report ID `2`, and 64-byte HID reports including the report ID. Read-only requests are `[1, 2, 0x80 | command, 0]` followed by 60 zero bytes. Queries are link state (`36`), charging (`37`), and battery status (`38`). Battery status is `[percent, millivolts_low, millivolts_high]`; `0..100` is valid and larger percentages are unavailable. Percentage is authoritative independently of the auxiliary voltage. Do not apply the ULX voltage curve. The receiver queries link state first; an inactive radio link skips battery status. The wired mouse queries only charging and battery status, because a radio link is not required. Both transports return live state of charge during charging. A failed wired query closes the handle and returns only the verified USB-presence flag, without claiming a current percentage or charging state.

Protocol evidence: the public [Xpanel application](https://xpanel.finalmouse.com/) inspected on 2026-10-08. Its `idjvmUDg.js` bundle selected report IDs `1`/`2` for SLX and decoded `CMD_ID_BATTERY_STATUS` as state of charge plus voltage; `YNk7IF1T.js` and `ByjTDMi_.js` mapped SLX mouse/receiver families. A live receiver capture returned link `[1]`, charging `[0]`, status `[42, 4, 15]`, or 42% at 3,844 mV. The regression suite covers this capture without hardware identifiers or serials.

ULX retains `%LOCALAPPDATA%\finalmouse-tray` and its legacy mutex. SLX uses `%LOCALAPPDATA%\slx-finalmouse-battery-tray` and `Local\SlxFinalmouseBatteryTray`. Neither version imports the other mouse's battery or charge history. Stop helpers target their own script paths and state. The same filename in another installation is not sufficient authority to stop it.

At most one receiver handle remains open. Each status query shares a 350 ms response deadline and 64-report limit between queue draining and response reading. Synchronous OS enumeration, open, write, and close calls are outside that response-time guarantee. Failed reads close the handle for rediscovery. Polling and manual actions serialize reading and applying results to prevent stale charge-history updates.

`finalmouse_tray.py` owns the tray UI, native polling, and charge tracking. Live charging readings carry the current percentage while the saved session start stays fixed. A fresh noncharging percentage can finish history over USB or wireless. The displayed number is white when not charging; unknown readings use `--`. Transitions use six bounded steps over about 180 ms in the existing update thread and stop promptly on shutdown. The existing poll loop advances a 1.2-second grey-to-white charging pulse without increasing the HID query rate or adding a worker. Pulse phase uses monotonic time and survives percentage changes and refreshes. At most eight images and native icon handles are cached for the repeated frames, then released on replacement or shutdown; `cached_icon.py` prevents per-frame ICO file serialization. Windows client-area animation settings disable the transition when requested. Tooltip text is capped at 127 characters, with full history in the dynamic Charge details submenu. Polling reuses the receiver handle; refresh and reconnect request a new connection.

On Windows, a virtual environment can retain a small Python redirector process. Startup excludes only the current interpreter's verified redirector from duplicate detection. The named mutex and other app-instance checks remain active.

[Back to installation and usage](../README.md)
