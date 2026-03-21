# BDFFHD Ultrawide Mod

Ultrawide support for **Bravely Default: Flying Fairy HD Remaster** on PC (Steam).

Removes black bars and renders the game at your monitor's native resolution.
Works with 21:9, 32:9, and any custom aspect ratio.

---

## Choose Your Install Method

### Option A: DLL Patcher (Easiest — Recommended)

**Zero dependencies. One file. Double-click and done.**

1. Download `BDFFHD_Ultrawide_Patcher.exe`
2. Double-click it
3. Pick your resolution from the menu
4. Launch the game — done!

> The patcher auto-finds your game folder, backs up your files, and patches
> the game DLL + Windows registry in one shot. To undo everything, run it
> again and pick "Restore original".

---

### Option B: BepInEx Mod (One-Click Installer)

**Runtime mod — no game files modified. Fully reversible by deleting one folder.**

1. Double-click `OneClick_Install.bat`
2. It downloads BepInEx and installs the mod automatically
3. Launch the game once, then close it (BepInEx initializes)
4. Edit `BepInEx\config\com.community.bdffhd.ultrawide.cfg` with your resolution
5. Launch again — enjoy!

> Requires internet for first install (downloads ~3MB BepInEx framework).
> After that, everything works offline.

---

## Supported Resolutions

| Resolution | Aspect Ratio | Name |
|---|---|---|
| 2560x1080 | 21:9 | Ultrawide 1080p |
| 3440x1440 | 21:9 | Ultrawide 1440p |
| 3840x1080 | 32:9 | Super Ultrawide 1080p |
| 5120x1440 | 32:9 | Super Ultrawide 1440p |
| Custom | Any | Enter your own |

## Which Option Should I Pick?

| | Option A (Patcher) | Option B (BepInEx Mod) |
|---|---|---|
| **Ease of use** | ★★★★★ | ★★★★ |
| **Dependencies** | None | Internet (first time) |
| **How it works** | Patches game DLL directly | Runs in memory at runtime |
| **Game files modified** | Yes (with auto-backup) | No |
| **Survives game updates** | No — re-run patcher | No — re-run installer |
| **Undo method** | Run patcher → Restore | Delete BepInEx folder |
| **UI fix quality** | Basic (aspect only) | Full (UI scaling + cleanup) |

**TL;DR:** Option A if you want the absolute simplest experience. Option B if you want cleaner UI scaling.

## Known Limitations

- **Title screen** may appear slightly stretched (pre-rendered 16:9 artwork)
- **Pre-rendered cutscenes** play at their original 16:9 aspect ratio
- **World map zoom-out** may show unrendered edges at extreme widths
- **Some menus** designed for 16:9 may have minor layout quirks

## Uninstallation

**Option A:** Run the patcher again → select "Restore original"
(or Steam → Right-click game → Properties → Verify Integrity)

**Option B:** Delete the `BepInEx` folder from your game directory
(or Steam → Verify Integrity)

## Troubleshooting

**Patcher says "Game not found":**
- Enter your game path manually when prompted
- Find it in Steam: Right-click BDFFHD → Manage → Browse Local Files

**Still seeing black bars (Option A):**
- Make sure the game is set to Fullscreen or Borderless in graphics settings
- Re-run the patcher if you changed resolution

**Game crashes on launch (Option B):**
- Make sure you launched once after installing BepInEx (it needs to initialize)
- Check `BepInEx\LogOutput.log` for error details
- Try removing the mod DLL, launching vanilla, then re-adding it

**Windows SmartScreen warning on the .exe:**
- This is normal for community tools. Click "More info" → "Run anyway"
- The patcher is open source — check the code yourself if unsure

## How It Works

**Option A** patches float constants inside `GameAssembly.dll` — the aspect ratio,
inverse ratio, and viewport centering values that Unity hardcoded for 16:9.

**Option B** uses [BepInEx](https://github.com/BepInEx/BepInEx) + [Harmony](https://github.com/pardeike/Harmony)
to intercept Camera and UI calls at runtime, forcing ultrawide rendering without
modifying any files on disk.

## Credits

- Built with [BepInEx 6](https://github.com/BepInEx/BepInEx) and [Harmony](https://github.com/pardeike/Harmony)
- Created by the community for the community
- Special thanks to r/bravelydefault

## License

Free to use, modify, and distribute. No warranty provided.
BepInEx is licensed under LGPL-2.1 — see BepInEx LICENSE file.
