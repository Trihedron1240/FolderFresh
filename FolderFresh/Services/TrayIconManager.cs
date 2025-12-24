using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace FolderFresh.Services;

/// <summary>
/// Manages the system tray icon and context menu
/// </summary>
public class TrayIconManager : IDisposable
{
    private NotifyIcon? _notifyIcon;
    private ContextMenuStrip? _contextMenu;
    private ToolStripMenuItem? _pauseResumeItem;
    private bool _isPaused;
    private bool _disposed;

    public event EventHandler? OpenRequested;
    public event EventHandler? CloseRequested;
    public event EventHandler<bool>? PauseStateChanged;

    public bool IsPaused => _isPaused;

    public void Initialize()
    {
        if (_notifyIcon != null) return;

        _contextMenu = new ContextMenuStrip();

        // Open
        var openItem = new ToolStripMenuItem("Open FolderFresh");
        openItem.Click += (s, e) => OpenRequested?.Invoke(this, EventArgs.Empty);
        openItem.Font = new Font(openItem.Font, FontStyle.Bold);
        _contextMenu.Items.Add(openItem);

        _contextMenu.Items.Add(new ToolStripSeparator());

        // Pause/Resume watched folders
        _pauseResumeItem = new ToolStripMenuItem("Pause Watched Folders");
        _pauseResumeItem.Click += PauseResumeItem_Click;
        _contextMenu.Items.Add(_pauseResumeItem);

        _contextMenu.Items.Add(new ToolStripSeparator());

        // Close
        var closeItem = new ToolStripMenuItem("Exit");
        closeItem.Click += (s, e) => CloseRequested?.Invoke(this, EventArgs.Empty);
        _contextMenu.Items.Add(closeItem);

        _notifyIcon = new NotifyIcon
        {
            Text = "FolderFresh",
            ContextMenuStrip = _contextMenu,
            Visible = false
        };

        // Try to load the icon
        LoadIcon();

        // Only open on left double-click, not right-click
        _notifyIcon.MouseDoubleClick += (s, e) =>
        {
            if (e.Button == MouseButtons.Left)
            {
                OpenRequested?.Invoke(this, EventArgs.Empty);
            }
        };
    }

    private void LoadIcon()
    {
        if (_notifyIcon == null) return;

        try
        {
            // Try to find the icon in the application directory
            var exePath = Environment.ProcessPath;
            if (!string.IsNullOrEmpty(exePath))
            {
                var iconPath = Path.Combine(Path.GetDirectoryName(exePath)!, "icon.ico");
                if (File.Exists(iconPath))
                {
                    _notifyIcon.Icon = new Icon(iconPath);
                    return;
                }
            }

            // Fallback: Use the application icon
            _notifyIcon.Icon = Icon.ExtractAssociatedIcon(Environment.ProcessPath ?? "");
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[TrayIconManager] Failed to load icon: {ex.Message}");
            // Use a default system icon as last resort
            _notifyIcon.Icon = SystemIcons.Application;
        }
    }

    private void PauseResumeItem_Click(object? sender, EventArgs e)
    {
        _isPaused = !_isPaused;
        UpdatePauseMenuItem();
        PauseStateChanged?.Invoke(this, _isPaused);
    }

    private void UpdatePauseMenuItem()
    {
        if (_pauseResumeItem != null)
        {
            _pauseResumeItem.Text = _isPaused ? "Resume Watched Folders" : "Pause Watched Folders";
        }

        if (_notifyIcon != null)
        {
            _notifyIcon.Text = _isPaused ? "FolderFresh (Paused)" : "FolderFresh";
        }
    }

    public void SetPauseState(bool isPaused)
    {
        _isPaused = isPaused;
        UpdatePauseMenuItem();
    }

    public void Show()
    {
        if (_notifyIcon != null)
        {
            _notifyIcon.Visible = true;
        }
    }

    public void Hide()
    {
        if (_notifyIcon != null)
        {
            _notifyIcon.Visible = false;
        }
    }

    public void ShowBalloonTip(string title, string text, ToolTipIcon icon = ToolTipIcon.Info, int timeout = 3000)
    {
        if (_notifyIcon == null) return;

        // Ensure the tray icon is visible - balloon tips only work when visible
        var wasVisible = _notifyIcon.Visible;
        if (!wasVisible)
        {
            _notifyIcon.Visible = true;
        }

        _notifyIcon.ShowBalloonTip(timeout, title, text, icon);

        // If we made it visible just for the notification, hide it after the balloon closes
        if (!wasVisible)
        {
            // Use a timer to hide after the balloon tip duration
            var hideTimer = new System.Threading.Timer(_ =>
            {
                try
                {
                    if (_notifyIcon != null && !_disposed)
                    {
                        _notifyIcon.Visible = false;
                    }
                }
                catch { }
            }, null, timeout + 500, System.Threading.Timeout.Infinite);
        }
    }

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;

        if (disposing)
        {
            if (_notifyIcon != null)
            {
                _notifyIcon.Visible = false;
                _notifyIcon.Dispose();
                _notifyIcon = null;
            }

            _contextMenu?.Dispose();
            _contextMenu = null;
        }

        _disposed = true;
    }
}
