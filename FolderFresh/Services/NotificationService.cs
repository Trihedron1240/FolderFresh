using System;
using System.Diagnostics;
using Microsoft.Windows.AppNotifications;
using Microsoft.Windows.AppNotifications.Builder;

namespace FolderFresh.Services;

/// <summary>
/// Service for showing Windows toast notifications using Windows App SDK
/// </summary>
public class NotificationService
{
    private static NotificationService? _instance;
    private static readonly object _lock = new();
    private bool _initialized;

    public static NotificationService Instance
    {
        get
        {
            if (_instance == null)
            {
                lock (_lock)
                {
                    _instance ??= new NotificationService();
                }
            }
            return _instance;
        }
    }

    private NotificationService() { }

    public void Initialize()
    {
        if (_initialized) return;

        try
        {
            var notificationManager = AppNotificationManager.Default;
            notificationManager.Register();
            _initialized = true;
            Debug.WriteLine("[NotificationService] Initialized successfully");
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[NotificationService] Failed to initialize: {ex.Message}");
        }
    }

    public void ShowNotification(string title, string message)
    {
        if (!_initialized)
        {
            Debug.WriteLine("[NotificationService] Not initialized, attempting to initialize...");
            Initialize();
        }

        try
        {
            var builder = new AppNotificationBuilder()
                .AddText(title)
                .AddText(message);

            var notification = builder.BuildNotification();
            AppNotificationManager.Default.Show(notification);
            Debug.WriteLine($"[NotificationService] Notification shown: {title} - {message}");
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[NotificationService] Failed to show notification: {ex.Message}");
        }
    }

    public void Unregister()
    {
        if (!_initialized) return;

        try
        {
            AppNotificationManager.Default.Unregister();
            _initialized = false;
            Debug.WriteLine("[NotificationService] Unregistered");
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[NotificationService] Failed to unregister: {ex.Message}");
        }
    }
}
