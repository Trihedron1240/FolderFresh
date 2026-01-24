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

    /// <summary>
    /// Validates and updates the startup registry entry if the executable path has changed.
    /// Should be called on app startup to ensure the registry points to the current exe.
    /// </summary>
    public static void ValidateAndUpdateStartupPath()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryRunPath, writable: true);
            if (key == null) return;

            var currentValue = key.GetValue(AppName) as string;
            if (string.IsNullOrEmpty(currentValue)) return;

            var currentExePath = Environment.ProcessPath;
            if (string.IsNullOrEmpty(currentExePath)) return;

            var expectedValue = $"\"{currentExePath}\" --minimized";

            // Check if the registry value matches the current exe path
            if (!currentValue.Equals(expectedValue, StringComparison.OrdinalIgnoreCase))
            {
                // Update the registry to point to the current exe
                key.SetValue(AppName, expectedValue);
                Debug.WriteLine($"[StartupManager] Updated startup path from '{currentValue}' to '{expectedValue}'");
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[StartupManager] Error validating startup path: {ex.Message}");
        }
    }
}
