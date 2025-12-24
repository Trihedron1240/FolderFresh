using System;
using System.Diagnostics;
using Microsoft.Win32;

namespace FolderFresh.Services;

/// <summary>
/// Manages Windows startup registration for the application
/// </summary>
public static class StartupManager
{
    private const string AppName = "FolderFresh";
    private const string RegistryRunPath = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";

    /// <summary>
    /// Sets whether the application should run on Windows startup
    /// </summary>
    public static void SetRunOnStartup(bool enable)
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryRunPath, writable: true);
            if (key == null)
            {
                Debug.WriteLine("[StartupManager] Failed to open registry key");
                return;
            }

            if (enable)
            {
                var exePath = Environment.ProcessPath;
                if (!string.IsNullOrEmpty(exePath))
                {
                    // Add --minimized argument so the app starts in tray if configured
                    key.SetValue(AppName, $"\"{exePath}\" --minimized");
                    Debug.WriteLine($"[StartupManager] Added to startup: {exePath}");
                }
            }
            else
            {
                key.DeleteValue(AppName, throwOnMissingValue: false);
                Debug.WriteLine("[StartupManager] Removed from startup");
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[StartupManager] Error setting startup: {ex.Message}");
        }
    }

    /// <summary>
    /// Checks if the application is registered to run on Windows startup
    /// </summary>
    public static bool IsRunOnStartupEnabled()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryRunPath);
            if (key == null) return false;

            var value = key.GetValue(AppName);
            return value != null;
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[StartupManager] Error checking startup: {ex.Message}");
            return false;
        }
    }
}
