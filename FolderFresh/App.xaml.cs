using Microsoft.UI.Xaml;
using Microsoft.UI.Windowing;
using System;
using FolderFresh.Services;
using FolderFresh.Models;

namespace FolderFresh;

public partial class App : Application
{
    public static Window? MainWindow { get; private set; }
    private static MainPage? _mainPage;
    private static TrayIconManager? _trayIconManager;

    /// <summary>
    /// Provides access to the tray icon manager for showing notifications
    /// </summary>
    public static TrayIconManager? TrayIconManager => _trayIconManager;
    private static SettingsService? _settingsService;
    private static bool _isExiting;
    private static AppWindow? _appWindow;

    /// <summary>
    /// Whether watched folders are globally paused from the tray icon.
    /// </summary>
    public static bool IsWatchersPaused => _trayIconManager?.IsPaused ?? false;

    public App()
    {
        this.InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        _settingsService = new SettingsService();
        var settings = _settingsService.GetSettings();

        // Validate/update startup registry if app is configured to run on startup
        // This ensures the registry points to the current exe path if it was moved
        if (settings.RunOnStartup)
        {
            StartupManager.ValidateAndUpdateStartupPath();
        }

        // Check for --minimized command line argument
        var cmdArgs = Environment.GetCommandLineArgs();
        var startMinimized = settings.StartMinimized || Array.Exists(cmdArgs, arg => arg.Equals("--minimized", StringComparison.OrdinalIgnoreCase));

        _mainPage = new MainPage();
        MainWindow = new Window
        {
            Title = "FolderFresh 3.0.1 Beta",
            Content = _mainPage
        };

        _appWindow = MainWindow.AppWindow;

        // Set window icon
        SetWindowIcon();

        // Customize title bar colors
        CustomizeTitleBar();

        // Set window size (1100x600 with sidebar)
        _appWindow.Resize(new Windows.Graphics.SizeInt32(1100, 600));

        // Center on screen
        var displayArea = DisplayArea.Primary;
        var centerX = (displayArea.WorkArea.Width - 1100) / 2;
        var centerY = (displayArea.WorkArea.Height - 600) / 2;
        _appWindow.Move(new Windows.Graphics.PointInt32(centerX, centerY));

        // Initialize tray icon
        InitializeTrayIcon();

        // Initialize notification service
        NotificationService.Instance.Initialize();

        // Subscribe to window events
        MainWindow.Closed += MainWindow_Closed;
        _appWindow.Closing += AppWindow_Closing;

        // Handle minimize to tray
        if (_appWindow.Presenter is OverlappedPresenter presenter)
        {
            // We need to detect when the window is minimized
            // Unfortunately WinUI 3 doesn't have a direct minimize event,
            // so we use the Changed event on the AppWindow
            _appWindow.Changed += AppWindow_Changed;
        }

        // Handle start minimized
        if (startMinimized && settings.MinimizeToTray)
        {
            // Start minimized to tray
            _trayIconManager?.Show();
            // Don't activate the window - it stays hidden
        }
        else if (startMinimized)
        {
            // Start minimized to taskbar
            MainWindow.Activate();
            MinimizeWindow();
        }
        else
        {
            MainWindow.Activate();
        }
    }

    private static void InitializeTrayIcon()
    {
        _trayIconManager = new TrayIconManager();
        _trayIconManager.Initialize();

        _trayIconManager.OpenRequested += (s, e) =>
        {
            ShowWindow();
        };

        _trayIconManager.CloseRequested += (s, e) =>
        {
            ExitApplication();
        };

        _trayIconManager.PauseStateChanged += async (s, isPaused) =>
        {
            if (_mainPage == null) return;

            if (isPaused)
            {
                await _mainPage.PauseAllWatchersAsync();
            }
            else
            {
                await _mainPage.StartAllWatchersAsync();
            }
        };
    }

    private static void AppWindow_Changed(AppWindow sender, AppWindowChangedEventArgs args)
    {
        // Check if the window was minimized
        if (args.DidPresenterChange && _appWindow?.Presenter is OverlappedPresenter presenter)
        {
            // Check if minimized
            if (presenter.State == OverlappedPresenterState.Minimized)
            {
                // Reload settings to get latest value
                _settingsService?.ClearCache();
                var settings = _settingsService?.GetSettings();

                if (settings?.MinimizeToTray == true)
                {
                    // Hide to tray instead of staying minimized on taskbar
                    HideToTray();
                }
            }
        }
    }

    private static void AppWindow_Closing(AppWindow sender, AppWindowClosingEventArgs args)
    {
        if (_isExiting) return;

        // Reload settings to get the latest value
        _settingsService?.ClearCache();
        var settings = _settingsService?.GetSettings();

        if (settings?.CloseToTray == true)
        {
            // Cancel the close and minimize to tray instead
            args.Cancel = true;
            HideToTray();
        }
        // If CloseToTray is false, let the close proceed normally (don't cancel)
    }

    private static async void MainWindow_Closed(object sender, WindowEventArgs args)
    {
        if (_isExiting) return;

        // Stop all folder watchers before closing
        _mainPage?.StopAllWatchers();

        // Save current profile state before closing
        if (_mainPage != null)
        {
            await _mainPage.SaveCurrentProfileStateAsync();
        }

        // Dispose tray icon
        _trayIconManager?.Dispose();
    }

    public static void ShowWindow()
    {
        if (MainWindow == null || _appWindow == null) return;

        _trayIconManager?.Hide();

        // Show the window (unhide it)
        _appWindow.Show();
        MainWindow.Activate();

        // Restore window if minimized
        if (_appWindow.Presenter is OverlappedPresenter presenter)
        {
            presenter.Restore();
        }
    }

    public static void MinimizeWindow()
    {
        if (_appWindow?.Presenter is OverlappedPresenter presenter)
        {
            presenter.Minimize();
        }
    }

    public static void HideToTray()
    {
        if (_appWindow == null) return;

        _trayIconManager?.Show();

        // Hide the window completely - removes from taskbar and alt-tab
        _appWindow.Hide();
    }

    public static void MinimizeToTrayIfEnabled()
    {
        var settings = _settingsService?.GetSettings();
        if (settings?.MinimizeToTray == true)
        {
            HideToTray();
        }
    }

    public static async void ExitApplication()
    {
        if (_isExiting) return;
        _isExiting = true;

        // Stop all folder watchers
        _mainPage?.StopAllWatchers();

        // Save current profile state
        if (_mainPage != null)
        {
            await _mainPage.SaveCurrentProfileStateAsync();
        }

        // Dispose tray icon
        _trayIconManager?.Dispose();

        // Unregister notification service
        NotificationService.Instance.Unregister();

        // Close the window
        MainWindow?.Close();

        // Exit the application
        Environment.Exit(0);
    }

    private static void SetWindowIcon()
    {
        if (_appWindow == null) return;

        try
        {
            // Try to find the icon in the application directory
            var exePath = Environment.ProcessPath;
            if (!string.IsNullOrEmpty(exePath))
            {
                var iconPath = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(exePath)!, "icon.ico");
                if (System.IO.File.Exists(iconPath))
                {
                    _appWindow.SetIcon(iconPath);
                }
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[App] Failed to set window icon: {ex.Message}");
        }
    }

    private static void CustomizeTitleBar()
    {
        if (_appWindow == null) return;

        try
        {
            var titleBar = _appWindow.TitleBar;

            // Dark purple background to match app theme (#1a1a2e or similar)
            var backgroundColor = Windows.UI.Color.FromArgb(255, 26, 26, 46);
            var foregroundColor = Windows.UI.Color.FromArgb(255, 255, 255, 255);
            var inactiveBackgroundColor = Windows.UI.Color.FromArgb(255, 20, 20, 36);
            var inactiveForegroundColor = Windows.UI.Color.FromArgb(255, 150, 150, 150);

            // Button hover color (slightly lighter purple)
            var buttonHoverBackgroundColor = Windows.UI.Color.FromArgb(255, 45, 45, 75);
            var buttonPressedBackgroundColor = Windows.UI.Color.FromArgb(255, 60, 60, 100);

            titleBar.BackgroundColor = backgroundColor;
            titleBar.ForegroundColor = foregroundColor;
            titleBar.InactiveBackgroundColor = inactiveBackgroundColor;
            titleBar.InactiveForegroundColor = inactiveForegroundColor;

            titleBar.ButtonBackgroundColor = backgroundColor;
            titleBar.ButtonForegroundColor = foregroundColor;
            titleBar.ButtonHoverBackgroundColor = buttonHoverBackgroundColor;
            titleBar.ButtonHoverForegroundColor = foregroundColor;
            titleBar.ButtonPressedBackgroundColor = buttonPressedBackgroundColor;
            titleBar.ButtonPressedForegroundColor = foregroundColor;

            titleBar.ButtonInactiveBackgroundColor = inactiveBackgroundColor;
            titleBar.ButtonInactiveForegroundColor = inactiveForegroundColor;
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[App] Failed to customize title bar: {ex.Message}");
        }
    }
}
