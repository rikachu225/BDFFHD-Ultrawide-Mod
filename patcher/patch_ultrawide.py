"""
BDFFHD Ultrawide Patcher v2.0
==============================
Patches Bravely Default: Flying Fairy HD Remaster for ultrawide monitors.

Engine: Unity 6 (6000.0.37f1) / IL2CPP
Target: GameAssembly.dll + Windows Registry (Unity player prefs)

Patch layers:
  1. Aspect ratio constant (camera projection)
  2. Inverse aspect ratio (viewport calculations)
  3. Half-resolution constants (viewport centering)
  4. Registry resolution override (force native ultrawide)

Supports: 21:9 and 32:9 resolutions
Author: Community tool — free for everyone
"""

import struct
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

# ─── Resolution Presets ──────────────────────────────────────────────────────

PRESETS = {
    "1": {"name": "2560x1080  (21:9)",   "w": 2560,  "h": 1080},
    "2": {"name": "3440x1440  (21:9)",   "w": 3440,  "h": 1440},
    "3": {"name": "3840x1600  (21:9)",   "w": 3840,  "h": 1600},
    "4": {"name": "5120x2160  (21:9)",   "w": 5120,  "h": 2160},
    "5": {"name": "3840x1080  (32:9)",   "w": 3840,  "h": 1080},
    "6": {"name": "5120x1440  (32:9)",   "w": 5120,  "h": 1440},
    "7": {"name": "Restore original 16:9", "w": 1920, "h": 1080},
}

# Original 16:9 values (what we search for and replace)
ORIG_W = 1920
ORIG_H = 1080
ORIG_RATIO     = 16.0 / 9.0        # 1.777778
ORIG_INV_RATIO = 9.0 / 16.0        # 0.562500
ORIG_HALF_H    = ORIG_H / 2.0      # 540.0
ORIG_HALF_W    = ORIG_W / 2.0      # 960.0

# ─── Patch Targets ───────────────────────────────────────────────────────────
# Each target: (offset, original_float, description, value_type)
# value_type determines how to calculate the replacement value

PATCH_TARGETS = [
    # Primary aspect ratio constant — camera projection matrix
    (0x0243C530, ORIG_RATIO,     "Aspect ratio (camera projection)",  "ratio"),
    # Inverse aspect ratio — viewport height/width calculation
    (0x0243C5B0, ORIG_INV_RATIO, "Inverse ratio (viewport calc)",     "inv_ratio"),
    # Half-height — viewport centering
    (0x0243C5B4, ORIG_HALF_H,    "Half-height (viewport center Y)",   "half_h"),
    # Half-width — viewport centering
    (0x0243C5B8, ORIG_HALF_W,    "Half-width (viewport center X)",    "half_w"),
]

REGISTRY_KEY = r"Software\SquareEnix\BDFFHD"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def find_game_dir():
    """Try common Steam install paths across drives."""
    drives = ["C", "D", "E", "F", "G", "H"]
    paths = []
    for d in drives:
        paths.append(Path(f"{d}:/SteamLibrary/steamapps/common/BDFFHD"))
        paths.append(Path(f"{d}:/Program Files (x86)/Steam/steamapps/common/BDFFHD"))
        paths.append(Path(f"{d}:/Program Files/Steam/steamapps/common/BDFFHD"))
        paths.append(Path(f"{d}:/Games/Steam/steamapps/common/BDFFHD"))
    for p in paths:
        if (p / "GameAssembly.dll").exists():
            return p
    return None


def calc_replacement(value_type: str, w: int, h: int) -> float:
    """Calculate the replacement value based on the target resolution."""
    if value_type == "ratio":
        return w / h
    elif value_type == "inv_ratio":
        return h / w
    elif value_type == "half_h":
        return h / 2.0
    elif value_type == "half_w":
        return w / 2.0
    raise ValueError(f"Unknown value_type: {value_type}")


def backup_file(filepath: Path) -> Path:
    """Create a timestamped backup. Preserves .original on first run."""
    backup_dir = filepath.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{filepath.name}.{timestamp}.bak"

    original_path = backup_dir / f"{filepath.name}.original"
    if not original_path.exists():
        shutil.copy2(filepath, original_path)
        print(f"  [BACKUP] Original saved: {original_path.name}")

    shutil.copy2(filepath, backup_path)
    print(f"  [BACKUP] Timestamped:    {backup_path.name}")
    return original_path


def restore_original(game_dir: Path) -> bool:
    """Restore from .original backup."""
    dll_path = game_dir / "GameAssembly.dll"
    original = game_dir / "backups" / "GameAssembly.dll.original"

    if not original.exists():
        print("  [ERROR] No original backup found.")
        print("         Use Steam > Right-click > Properties > Verify Integrity instead.")
        return False

    shutil.copy2(original, dll_path)
    print("  [OK] GameAssembly.dll restored to original.")
    return True


def restore_registry():
    """Restore registry to default 1920x1080."""
    if not HAS_WINREG:
        return
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Screenmanager Resolution Width_h182942802", 0, winreg.REG_DWORD, 1920)
        winreg.SetValueEx(key, "Screenmanager Resolution Height_h2627697771", 0, winreg.REG_DWORD, 1080)
        winreg.SetValueEx(key, "Screenmanager Resolution Window Width_h2524650974", 0, winreg.REG_DWORD, 1920)
        winreg.SetValueEx(key, "Screenmanager Resolution Window Height_h1684712807", 0, winreg.REG_DWORD, 1080)
        winreg.SetValueEx(key, "Screenmanager Resolution Use Native_h1405027254", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        print("  [OK] Registry restored to 1920x1080.")
    except OSError as e:
        print(f"  [WARN] Could not restore registry: {e}")


def patch_registry(w: int, h: int):
    """Force game resolution via Unity's registry player prefs."""
    if not HAS_WINREG:
        print("  [SKIP] winreg not available (non-Windows?). Set resolution manually.")
        return

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Screenmanager Resolution Width_h182942802", 0, winreg.REG_DWORD, w)
        winreg.SetValueEx(key, "Screenmanager Resolution Height_h2627697771", 0, winreg.REG_DWORD, h)
        winreg.SetValueEx(key, "Screenmanager Resolution Window Width_h2524650974", 0, winreg.REG_DWORD, w)
        winreg.SetValueEx(key, "Screenmanager Resolution Window Height_h1684712807", 0, winreg.REG_DWORD, h)
        winreg.SetValueEx(key, "Screenmanager Resolution Use Native_h1405027254", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(key, "Screenmanager Fullscreen mode_h3630240806", 0, winreg.REG_DWORD, 3)
        winreg.CloseKey(key)
        print(f"  [OK] Registry set to {w}x{h} borderless fullscreen.")
    except FileNotFoundError:
        print("  [WARN] Registry key not found. Launch the game once first, then re-run.")
    except OSError as e:
        print(f"  [WARN] Could not update registry: {e}")


def patch_dll(game_dir: Path, w: int, h: int, preset_name: str) -> bool:
    """Apply all patches to GameAssembly.dll."""
    dll_path = game_dir / "GameAssembly.dll"

    if not dll_path.exists():
        print(f"  [ERROR] GameAssembly.dll not found at {dll_path}")
        return False

    print(f"\n  Reading {dll_path.name} ({dll_path.stat().st_size:,} bytes)...")
    with open(dll_path, 'rb') as f:
        data = bytearray(f.read())

    patches_applied = 0
    patches_skipped = 0

    print(f"\n  --- DLL Patches ---")

    for offset, expected_orig, description, value_type in PATCH_TARGETS:
        if offset + 4 > len(data):
            print(f"  [WARN] 0x{offset:08X}: beyond file size, skipping.")
            continue

        current_val = struct.unpack('<f', bytes(data[offset:offset+4]))[0]
        new_val = calc_replacement(value_type, w, h)
        new_bytes = struct.pack('<f', new_val)

        # Check if it matches original, is already our target, or something else
        if abs(current_val - new_val) < 0.001:
            print(f"  [SKIP] 0x{offset:08X}: {description}")
            print(f"         Already set to {current_val:.6f}")
            patches_skipped += 1
            continue

        is_original = abs(current_val - expected_orig) < 0.01
        status = "original" if is_original else f"modified ({current_val:.6f})"

        data[offset:offset+4] = new_bytes
        print(f"  [PATCH] 0x{offset:08X}: {description}")
        print(f"          {current_val:.6f} -> {new_val:.6f}  ({status})")
        patches_applied += 1

    # Also scan for any other occurrences of the aspect ratio constant
    # that might be in a different location (game updates can shift offsets)
    orig_ratio_bytes = struct.pack('<f', ORIG_RATIO)
    idx = 0
    extra_found = 0
    new_ratio = w / h
    new_ratio_bytes = struct.pack('<f', new_ratio)

    while True:
        idx = data.find(orig_ratio_bytes, idx)
        if idx == -1:
            break
        # Skip if already handled
        if any(idx == t[0] for t in PATCH_TARGETS):
            idx += 1
            continue
        # Check if it's a game constant (next float is 2*PI)
        if idx + 8 <= len(data):
            next_val = struct.unpack('<f', bytes(data[idx+4:idx+8]))[0]
            if abs(next_val - 6.283185) < 0.01:
                data[idx:idx+4] = new_ratio_bytes
                print(f"  [PATCH] 0x{idx:08X}: Aspect ratio (auto-detected game constant)")
                print(f"          {ORIG_RATIO:.6f} -> {new_ratio:.6f}")
                patches_applied += 1
                extra_found += 1
        idx += 1

    if patches_applied == 0 and patches_skipped > 0:
        print(f"\n  All {patches_skipped} targets already patched to this resolution.")
        return True

    if patches_applied == 0:
        print("\n  [WARN] No patches applied! Game may have updated.")
        print("         Try Steam > Verify Integrity, then re-run.")
        return False

    # Backup and write
    print(f"\n  Creating backup...")
    backup_file(dll_path)

    print(f"  Writing patched DLL...")
    with open(dll_path, 'wb') as f:
        f.write(data)

    print(f"\n  {'='*55}")
    print(f"  DLL: {patches_applied} patch(es) applied for {preset_name}")
    print(f"  {'='*55}")
    return True


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print()
    print("  ╔═══════════════════════════════════════════════════════╗")
    print("  ║   BRAVELY DEFAULT: FLYING FAIRY HD REMASTER          ║")
    print("  ║   Ultrawide Patcher v2.0                             ║")
    print("  ║                                                      ║")
    print("  ║   Patches: DLL constants + Registry resolution       ║")
    print("  ║   Supports 21:9 and 32:9 resolutions                 ║")
    print("  ║   Free & open source — for the community             ║")
    print("  ╚═══════════════════════════════════════════════════════╝")
    print()

    # Find game directory
    game_dir = find_game_dir()

    if not game_dir:
        print("  Game not found in common Steam locations.")
        custom = input("  Enter your BDFFHD install path: ").strip().strip('"')
        if custom:
            game_dir = Path(custom)
            if not (game_dir / "GameAssembly.dll").exists():
                print("  [ERROR] GameAssembly.dll not found at that path.")
                input("\n  Press Enter to exit...")
                return
        else:
            print("  [ERROR] No path provided.")
            input("\n  Press Enter to exit...")
            return

    print(f"  Game found: {game_dir}")

    # Show current state
    dll_path = game_dir / "GameAssembly.dll"
    with open(dll_path, 'rb') as f:
        f.seek(PATCH_TARGETS[0][0])  # Read primary aspect ratio offset
        current_bytes = f.read(4)
    current_val = struct.unpack('<f', current_bytes)[0]

    if abs(current_val - ORIG_RATIO) < 0.001:
        print(f"  DLL status: UNMODIFIED (16:9 = {current_val:.6f})")
    else:
        print(f"  DLL status: PATCHED (ratio = {current_val:.6f})")

    # Check registry
    if HAS_WINREG:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_READ)
            reg_w = winreg.QueryValueEx(key, "Screenmanager Resolution Width_h182942802")[0]
            reg_h = winreg.QueryValueEx(key, "Screenmanager Resolution Height_h2627697771")[0]
            winreg.CloseKey(key)
            print(f"  Registry:   {reg_w}x{reg_h}")
        except OSError:
            print(f"  Registry:   Not found (launch game once first)")

    # Menu
    print()
    print("  ┌─────────────────────────────────────────────┐")
    print("  │  Select your resolution:                    │")
    print("  │                                             │")
    print("  │  --- 21:9 Ultrawide ---                     │")
    for key in ["1", "2", "3", "4"]:
        p = PRESETS[key]
        ratio = p["w"] / p["h"]
        print(f"  │  [{key}]  {p['name']:<22} ({ratio:.4f})    │")
    print("  │                                             │")
    print("  │  --- 32:9 Super Ultrawide ---               │")
    for key in ["5", "6"]:
        p = PRESETS[key]
        ratio = p["w"] / p["h"]
        print(f"  │  [{key}]  {p['name']:<22} ({ratio:.4f})    │")
    print("  │                                             │")
    print("  │  --- Restore ---                            │")
    print(f"  │  [7]  {PRESETS['7']['name']:<38} │")
    print("  │                                             │")
    print("  │  [C]  Custom resolution                     │")
    print("  │  [Q]  Quit                                  │")
    print("  └─────────────────────────────────────────────┘")
    print()

    choice = input("  Your choice: ").strip().upper()

    if choice == 'Q':
        print("  Bye!")
        return

    if choice == 'C':
        try:
            w = int(input("  Enter width  (e.g. 3440): ").strip())
            h = int(input("  Enter height (e.g. 1440): ").strip())
            if w <= 0 or h <= 0:
                raise ValueError
            preset_name = f"{w}x{h} (custom)"
        except (ValueError, ZeroDivisionError):
            print("  [ERROR] Invalid resolution.")
            input("\n  Press Enter to exit...")
            return
    elif choice == '7':
        print("\n  Restoring everything to original...")
        restore_original(game_dir)
        restore_registry()
        input("\n  Press Enter to exit...")
        return
    elif choice in PRESETS:
        p = PRESETS[choice]
        w, h = p["w"], p["h"]
        preset_name = p["name"]
    else:
        print(f"  [ERROR] Invalid choice: {choice}")
        input("\n  Press Enter to exit...")
        return

    ratio = w / h
    print(f"\n  Target: {preset_name}")
    print(f"  Resolution: {w}x{h}")
    print(f"  Aspect ratio: {ratio:.6f}")
    print()
    print(f"  Will patch:")
    print(f"    - GameAssembly.dll (4 constants)")
    print(f"    - Registry (force {w}x{h} borderless)")
    print()

    confirm = input("  Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  Cancelled.")
        input("\n  Press Enter to exit...")
        return

    # Patch DLL
    dll_ok = patch_dll(game_dir, w, h, preset_name)

    # Patch registry
    print(f"\n  --- Registry Patch ---")
    patch_registry(w, h)

    if dll_ok:
        print()
        print("  ┌──────────────────────────────────────────────────┐")
        print("  │  DONE! Launch the game to test.                  │")
        print("  │                                                  │")
        print("  │  The game should now start at your native        │")
        print("  │  ultrawide resolution automatically.             │")
        print("  │                                                  │")
        print("  │  If resolution resets in-game, change display    │")
        print("  │  mode to 'Borderless' in Graphics Settings.      │")
        print("  │                                                  │")
        print("  │  NOTES:                                          │")
        print("  │  - Game updates will revert the DLL patch        │")
        print("  │  - Re-run this patcher after any game update     │")
        print("  │  - Use option [7] to restore everything          │")
        print("  │  - Backups in: <game>/backups/                   │")
        print("  └──────────────────────────────────────────────────┘")

    input("\n  Press Enter to exit...")


if __name__ == "__main__":
    main()
