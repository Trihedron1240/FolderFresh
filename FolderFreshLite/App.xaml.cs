using Microsoft.UI.Xaml;

namespace FolderFreshLite;

public partial class App : Application
{
    public static Window? MainWindow { get; private set; }

    public App()
    {
        this.InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        MainWindow = new Window
        {
            Title = "FolderFresh Lite",
            Content = new MainPage()
        };

        // Set window size (1100x600 with sidebar)
        MainWindow.AppWindow.Resize(new Windows.Graphics.SizeInt32(1100, 600));
        
        // Center on screen
        var displayArea = Microsoft.UI.Windowing.DisplayArea.Primary;
        var centerX = (displayArea.WorkArea.Width - 1100) / 2;
        var centerY = (displayArea.WorkArea.Height - 600) / 2;
        MainWindow.AppWindow.Move(new Windows.Graphics.PointInt32(centerX, centerY));

        MainWindow.Activate();
    }
}
