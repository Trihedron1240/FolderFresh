using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using Microsoft.UI.Xaml.Media.Imaging;
using FolderFreshLite.Helpers;

namespace FolderFreshLite.Models;

public class FileItem : INotifyPropertyChanged
{
    private string _name = string.Empty;
    private string _path = string.Empty;
    private string _extension = string.Empty;
    private bool _isFolder;
    private ulong _size;
    private DateTime _dateModified;
    private BitmapImage? _thumbnail;
    private bool _isSelected;
    private bool _isRuleMatch;
    private string? _matchedRuleName;
    private string? _displayColor;
    private bool _isAlreadyOrganized;

    public string Name
    {
        get => _name;
        set => SetProperty(ref _name, value);
    }

    public string Path
    {
        get => _path;
        set => SetProperty(ref _path, value);
    }

    public string Extension
    {
        get => _extension;
        set => SetProperty(ref _extension, value);
    }

    public bool IsFolder
    {
        get => _isFolder;
        set => SetProperty(ref _isFolder, value);
    }

    public ulong Size
    {
        get => _size;
        set => SetProperty(ref _size, value);
    }

    public DateTime DateModified
    {
        get => _dateModified;
        set => SetProperty(ref _dateModified, value);
    }

    public BitmapImage? Thumbnail
    {
        get => _thumbnail;
        set => SetProperty(ref _thumbnail, value);
    }

    public bool IsSelected
    {
        get => _isSelected;
        set => SetProperty(ref _isSelected, value);
    }

    /// <summary>
    /// Whether this file was matched by a rule (vs category)
    /// </summary>
    public bool IsRuleMatch
    {
        get => _isRuleMatch;
        set => SetProperty(ref _isRuleMatch, value);
    }

    /// <summary>
    /// Name of the rule that matched this file (if IsRuleMatch is true)
    /// </summary>
    public string? MatchedRuleName
    {
        get => _matchedRuleName;
        set => SetProperty(ref _matchedRuleName, value);
    }

    /// <summary>
    /// Custom display color for the item (used for rules/categories)
    /// </summary>
    public string? DisplayColor
    {
        get => _displayColor;
        set => SetProperty(ref _displayColor, value);
    }

    /// <summary>
    /// Whether this file is already in its organized location
    /// </summary>
    public bool IsAlreadyOrganized
    {
        get => _isAlreadyOrganized;
        set => SetProperty(ref _isAlreadyOrganized, value);
    }

    public string DisplaySize
    {
        get
        {
            if (IsFolder) return string.Empty;
            if (Size < 1024) return $"{Size} B";
            if (Size < 1024 * 1024) return $"{Size / 1024.0:F1} KB";
            if (Size < 1024 * 1024 * 1024) return $"{Size / (1024.0 * 1024.0):F1} MB";
            return $"{Size / (1024.0 * 1024.0 * 1024.0):F2} GB";
        }
    }

    public string IconGlyph => FileIconHelper.GetIconGlyph(Extension, IsFolder);

    public string IconColor => FileIconHelper.GetIconColor(Extension, IsFolder);

    public string DisplayDate => DateModified.ToString("MMM d, yyyy h:mm tt");

    public string FileTypeDisplay
    {
        get
        {
            if (IsFolder) return "Folder";
            if (string.IsNullOrEmpty(Extension)) return "File";

            var ext = Extension.TrimStart('.').ToUpperInvariant();
            return ext switch
            {
                "PDF" => "PDF Document",
                "DOC" or "DOCX" => "Word Document",
                "XLS" or "XLSX" => "Excel Spreadsheet",
                "PPT" or "PPTX" => "PowerPoint",
                "TXT" => "Text Document",
                "RTF" => "Rich Text Document",
                "CSV" => "CSV File",
                "JPG" or "JPEG" => "JPEG Image",
                "PNG" => "PNG Image",
                "GIF" => "GIF Image",
                "BMP" => "Bitmap Image",
                "SVG" => "SVG Image",
                "WEBP" => "WebP Image",
                "ICO" => "Icon File",
                "MP3" => "MP3 Audio",
                "WAV" => "WAV Audio",
                "FLAC" => "FLAC Audio",
                "AAC" => "AAC Audio",
                "OGG" => "OGG Audio",
                "M4A" => "M4A Audio",
                "WMA" => "WMA Audio",
                "MP4" => "MP4 Video",
                "AVI" => "AVI Video",
                "MKV" => "MKV Video",
                "MOV" => "MOV Video",
                "WMV" => "WMV Video",
                "FLV" => "FLV Video",
                "WEBM" => "WebM Video",
                "ZIP" => "ZIP Archive",
                "RAR" => "RAR Archive",
                "7Z" => "7-Zip Archive",
                "TAR" => "TAR Archive",
                "GZ" => "GZip Archive",
                "CS" => "C# Source",
                "JS" => "JavaScript File",
                "TS" => "TypeScript File",
                "PY" => "Python File",
                "JAVA" => "Java File",
                "CPP" or "C" or "H" => "C/C++ File",
                "HTML" or "HTM" => "HTML File",
                "CSS" => "CSS File",
                "XAML" => "XAML File",
                "XML" => "XML File",
                "JSON" => "JSON File",
                "YAML" or "YML" => "YAML File",
                "EXE" => "Application",
                "MSI" => "Installer",
                "DLL" => "DLL File",
                "BAT" or "CMD" => "Batch File",
                "PS1" => "PowerShell Script",
                "SH" => "Shell Script",
                "TTF" or "OTF" => "Font File",
                "WOFF" or "WOFF2" => "Web Font",
                "DB" or "SQLITE" => "Database",
                "SQL" => "SQL File",
                "MD" => "Markdown",
                "LOG" => "Log File",
                "INI" or "CFG" or "CONF" => "Config File",
                _ => $"{ext} File"
            };
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }
}
