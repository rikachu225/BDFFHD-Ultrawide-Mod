using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;
using System;

namespace BDFFHD_UltrawideMod;

/// <summary>
/// Ultrawide support for Bravely Default Flying Fairy HD Remaster.
/// Supports 21:9, 32:9, and any custom aspect ratio.
///
/// How it works:
///   - Harmony patches on Camera.aspect/rect to force ultrawide projection
///   - CanvasScaler fix for proper UI positioning at non-16:9 ratios
///   - Hides off-screen UI elements revealed by wider viewport
///   - Blocks the game from resetting resolution to 16:9
/// </summary>
[BepInPlugin(PluginGUID, PluginName, PluginVersion)]
public class UltrawidePlugin : BasePlugin
{
    public const string PluginGUID = "com.community.bdffhd.ultrawide";
    public const string PluginName = "BDFFHD Ultrawide";
    public const string PluginVersion = "1.0.0";

    internal new static ManualLogSource Log;
    internal static float TargetAspect;
    internal static float OriginalAspect = 16f / 9f;
    internal static int TargetWidth;
    internal static int TargetHeight;

    internal static int CallCount = 0;
    internal static bool SceneCleaned = false;

    public override void Load()
    {
        Log = base.Log;

        var cfgWidth = Config.Bind("Resolution", "Width", 2560,
            "Your monitor's horizontal resolution (e.g. 2560, 3440, 3840, 5120)");
        var cfgHeight = Config.Bind("Resolution", "Height", 1080,
            "Your monitor's vertical resolution (e.g. 1080, 1440)");
        var cfgEnabled = Config.Bind("General", "Enabled", true,
            "Enable/disable the ultrawide mod");

        if (!cfgEnabled.Value) { Log.LogInfo("Mod disabled via config."); return; }

        TargetWidth = cfgWidth.Value;
        TargetHeight = cfgHeight.Value;
        TargetAspect = (float)TargetWidth / TargetHeight;

        if (Math.Abs(TargetAspect - OriginalAspect) < 0.01f)
        {
            Log.LogWarning("Configured resolution is 16:9 — ultrawide patch not needed.");
            Log.LogWarning("Edit BepInEx/config/com.community.bdffhd.ultrawide.cfg to set your resolution.");
            return;
        }

        string resStr = $"{TargetWidth}x{TargetHeight}";
        Log.LogInfo($"=== BDFFHD Ultrawide Mod v{PluginVersion} ===");
        Log.LogInfo($"Resolution: {resStr} | Aspect: {TargetAspect:F4} ({TargetAspect / OriginalAspect:F2}x wider)");

        try
        {
            Screen.SetResolution(TargetWidth, TargetHeight, FullScreenMode.FullScreenWindow);
        }
        catch (Exception ex) { Log.LogWarning($"SetResolution: {ex.Message}"); }

        var harmony = new Harmony(PluginGUID);
        harmony.PatchAll();
        Log.LogInfo("Harmony patches applied. Enjoy your ultrawide experience!");
    }

    /// <summary>
    /// Scene cleanup — fixes CanvasScalers, disables aspect enforcers,
    /// and hides UI elements that leak at wider aspect ratios.
    /// </summary>
    internal static void ScanAndCleanScene()
    {
        try
        {
            int fixCount = 0;

            // ── Fix CanvasScalers: use height-based matching ──
            var scalers = UnityEngine.Object.FindObjectsOfType<CanvasScaler>(true);
            for (int i = 0; i < scalers.Length; i++)
            {
                var scaler = scalers[i];
                if (scaler == null) continue;
                try
                {
                    if (scaler.uiScaleMode == CanvasScaler.ScaleMode.ScaleWithScreenSize &&
                        scaler.matchWidthOrHeight < 0.99f)
                    {
                        scaler.matchWidthOrHeight = 1f;
                        fixCount++;
                    }
                }
                catch { }
            }

            // ── Disable aspect enforcement components ──
            var allBehaviours = UnityEngine.Object.FindObjectsOfType<MonoBehaviour>(true);
            for (int i = 0; i < allBehaviours.Length; i++)
            {
                var mb = allBehaviours[i];
                if (mb == null) continue;
                try
                {
                    string typeName = mb.GetIl2CppType().Name;
                    if ((typeName.Contains("FixedAspect") ||
                         typeName.Contains("LetterBox") ||
                         typeName.Contains("AspectRatio") ||
                         typeName.Contains("AspectFitter")) && mb.enabled)
                    {
                        mb.enabled = false;
                        fixCount++;
                    }
                }
                catch { }
            }

            // ── Hide UI elements that leak at ultrawide ──
            var allTransforms = UnityEngine.Object.FindObjectsOfType<Transform>(true);
            for (int i = 0; i < allTransforms.Length; i++)
            {
                var t = allTransforms[i];
                if (t == null || !t.gameObject.activeSelf) continue;
                try
                {
                    string name = t.gameObject.name;
                    string nameLower = name.ToLower();

                    bool shouldHide =
                        // Off-screen menu drawer revealed by wider canvas
                        name == "Drawer" ||
                        // Minimap overflow panels
                        name.StartsWith("OverArea") ||
                        // Letterbox/blackbar overlays
                        nameLower.Contains("letterbox") ||
                        nameLower.Contains("pillarbox") ||
                        nameLower.Contains("blackbar") ||
                        nameLower.Contains("screenmask");

                    if (shouldHide)
                    {
                        t.gameObject.SetActive(false);
                        fixCount++;
                    }
                }
                catch { }
            }

            // ── Force all cameras to ultrawide ──
            var cameras = Camera.allCameras;
            for (int i = 0; i < cameras.Length; i++)
            {
                var cam = cameras[i];
                if (cam == null) continue;
                try
                {
                    cam.rect = new Rect(0f, 0f, 1f, 1f);
                    cam.aspect = TargetAspect;
                }
                catch { }
            }

            if (fixCount > 0)
            {
                Log.LogInfo($"Scene cleanup: {fixCount} fixes applied.");
                SceneCleaned = true;
            }
        }
        catch (Exception ex)
        {
            Log.LogError($"ScanAndCleanScene: {ex.Message}");
        }
    }
}

[HarmonyPatch]
public static class UltrawidePatches
{
    // ═══════════════════════════════════════════════════════════════
    // Camera.aspect — Force ultrawide ratio + trigger scene cleanup
    // ═══════════════════════════════════════════════════════════════
    [HarmonyPatch(typeof(Camera), nameof(Camera.aspect), MethodType.Setter)]
    [HarmonyPrefix]
    public static bool Camera_SetAspect(Camera __instance, ref float value)
    {
        value = UltrawidePlugin.TargetAspect;

        UltrawidePlugin.CallCount++;
        if (UltrawidePlugin.CallCount == 100 || UltrawidePlugin.CallCount == 500 ||
            UltrawidePlugin.CallCount == 2000 || UltrawidePlugin.CallCount == 5000 ||
            UltrawidePlugin.CallCount == 15000)
        {
            UltrawidePlugin.ScanAndCleanScene();
        }
        return true;
    }

    [HarmonyPatch(typeof(Camera), nameof(Camera.aspect), MethodType.Getter)]
    [HarmonyPostfix]
    public static void Camera_GetAspect(ref float __result)
    {
        __result = UltrawidePlugin.TargetAspect;
    }

    // ═══════════════════════════════════════════════════════════════
    // Camera.rect — Force full viewport (no letterbox)
    // ═══════════════════════════════════════════════════════════════
    [HarmonyPatch(typeof(Camera), nameof(Camera.rect), MethodType.Setter)]
    [HarmonyPrefix]
    public static bool Camera_SetRect(Camera __instance, ref Rect value)
    {
        value = new Rect(0f, 0f, 1f, 1f);
        return true;
    }

    [HarmonyPatch(typeof(Camera), nameof(Camera.rect), MethodType.Getter)]
    [HarmonyPostfix]
    public static void Camera_GetRect(ref Rect __result)
    {
        __result = new Rect(0f, 0f, 1f, 1f);
    }

    [HarmonyPatch(typeof(Camera), nameof(Camera.pixelRect), MethodType.Setter)]
    [HarmonyPrefix]
    public static bool Camera_SetPixelRect(Camera __instance, ref Rect value)
    {
        value = new Rect(0f, 0f, UltrawidePlugin.TargetWidth, UltrawidePlugin.TargetHeight);
        return true;
    }

    // ═══════════════════════════════════════════════════════════════
    // Screen.SetResolution — Prevent game from resetting to 16:9
    // ═══════════════════════════════════════════════════════════════
    [HarmonyPatch(typeof(Screen), nameof(Screen.SetResolution), typeof(int), typeof(int), typeof(FullScreenMode))]
    [HarmonyPrefix]
    public static bool Screen_SetRes3(ref int width, ref int height, ref FullScreenMode fullscreenMode)
    {
        width = UltrawidePlugin.TargetWidth;
        height = UltrawidePlugin.TargetHeight;
        fullscreenMode = FullScreenMode.FullScreenWindow;
        return true;
    }

    [HarmonyPatch(typeof(Screen), nameof(Screen.SetResolution), typeof(int), typeof(int), typeof(bool))]
    [HarmonyPrefix]
    public static bool Screen_SetRes2(ref int width, ref int height, ref bool fullscreen)
    {
        width = UltrawidePlugin.TargetWidth;
        height = UltrawidePlugin.TargetHeight;
        return true;
    }
}
