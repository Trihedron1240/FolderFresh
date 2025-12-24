using System;
using System.Collections.Generic;

namespace FolderFresh.Helpers;

public static class FileIconHelper
{
    private static readonly Dictionary<string, string> ExtensionGlyphs = new(StringComparer.OrdinalIgnoreCase)
    {
        // Documents
        { ".pdf", "\uEA90" },      // PDF icon
        { ".doc", "\uE8A5" },      // Document
        { ".docx", "\uE8A5" },
        { ".txt", "\uE8A5" },
        { ".rtf", "\uE8A5" },
        { ".odt", "\uE8A5" },

        // Spreadsheets
        { ".xls", "\uE80A" },      // Table/Grid
        { ".xlsx", "\uE80A" },
        { ".csv", "\uE80A" },
        { ".ods", "\uE80A" },

        // Presentations
        { ".ppt", "\uE8A1" },      // Slideshow
        { ".pptx", "\uE8A1" },
        { ".odp", "\uE8A1" },

        // Images
        { ".jpg", "\uEB9F" },      // Photo
        { ".jpeg", "\uEB9F" },
        { ".png", "\uEB9F" },
        { ".gif", "\uEB9F" },
        { ".bmp", "\uEB9F" },
        { ".ico", "\uEB9F" },
        { ".svg", "\uEB9F" },
        { ".webp", "\uEB9F" },
        { ".tiff", "\uEB9F" },
        { ".tif", "\uEB9F" },
        { ".raw", "\uEB9F" },

        // Audio
        { ".mp3", "\uE8D6" },      // Music/Audio
        { ".wav", "\uE8D6" },
        { ".flac", "\uE8D6" },
        { ".aac", "\uE8D6" },
        { ".ogg", "\uE8D6" },
        { ".wma", "\uE8D6" },
        { ".m4a", "\uE8D6" },

        // Video
        { ".mp4", "\uE8B2" },      // Video
        { ".avi", "\uE8B2" },
        { ".mkv", "\uE8B2" },
        { ".mov", "\uE8B2" },
        { ".wmv", "\uE8B2" },
        { ".flv", "\uE8B2" },
        { ".webm", "\uE8B2" },
        { ".m4v", "\uE8B2" },

        // Archives
        { ".zip", "\uF012" },      // Archive/Package
        { ".rar", "\uF012" },
        { ".7z", "\uF012" },
        { ".tar", "\uF012" },
        { ".gz", "\uF012" },
        { ".bz2", "\uF012" },

        // Code/Development
        { ".cs", "\uE943" },       // Code
        { ".js", "\uE943" },
        { ".ts", "\uE943" },
        { ".py", "\uE943" },
        { ".java", "\uE943" },
        { ".cpp", "\uE943" },
        { ".c", "\uE943" },
        { ".h", "\uE943" },
        { ".html", "\uE943" },
        { ".css", "\uE943" },
        { ".xaml", "\uE943" },
        { ".xml", "\uE943" },
        { ".json", "\uE943" },
        { ".yaml", "\uE943" },
        { ".yml", "\uE943" },

        // Executables
        { ".exe", "\uE756" },      // App/Settings
        { ".msi", "\uE756" },
        { ".bat", "\uE756" },
        { ".cmd", "\uE756" },
        { ".ps1", "\uE756" },
        { ".sh", "\uE756" },

        // Fonts
        { ".ttf", "\uE8D2" },      // Font
        { ".otf", "\uE8D2" },
        { ".woff", "\uE8D2" },
        { ".woff2", "\uE8D2" },

        // Database
        { ".db", "\uEE94" },       // Database
        { ".sqlite", "\uEE94" },
        { ".sql", "\uEE94" },
        { ".mdb", "\uEE94" },
    };

    public const string FolderGlyph = "\uE8B7";        // Folder icon
    public const string DefaultFileGlyph = "\uE7C3";  // Generic file icon

    public static string GetIconGlyph(string? extension, bool isFolder)
    {
        if (isFolder)
            return FolderGlyph;

        if (string.IsNullOrEmpty(extension))
            return DefaultFileGlyph;

        // Ensure extension starts with dot
        if (!extension.StartsWith('.'))
            extension = "." + extension;

        return ExtensionGlyphs.TryGetValue(extension, out var glyph)
            ? glyph
            : DefaultFileGlyph;
    }

    public static string GetIconColor(string? extension, bool isFolder)
    {
        if (isFolder)
            return "#FFD866"; // Yellow for folders

        if (string.IsNullOrEmpty(extension))
            return "#999999";

        if (!extension.StartsWith('.'))
            extension = "." + extension;

        return extension.ToLowerInvariant() switch
        {
            ".pdf" => "#FF6B6B",      // Red
            ".doc" or ".docx" or ".txt" or ".rtf" => "#5B9BD5",  // Blue
            ".xls" or ".xlsx" or ".csv" => "#70AD47",  // Green
            ".ppt" or ".pptx" => "#ED7D31",  // Orange
            ".jpg" or ".jpeg" or ".png" or ".gif" or ".bmp" or ".svg" or ".webp" => "#9B59B6",  // Purple
            ".mp3" or ".wav" or ".flac" or ".aac" or ".ogg" => "#E91E63",  // Pink
            ".mp4" or ".avi" or ".mkv" or ".mov" or ".wmv" => "#00BCD4",  // Cyan
            ".zip" or ".rar" or ".7z" or ".tar" or ".gz" => "#795548",  // Brown
            ".cs" or ".js" or ".ts" or ".py" or ".java" => "#4CAF50",  // Green
            ".html" or ".css" or ".xaml" or ".xml" => "#FF9800",  // Orange
            ".exe" or ".msi" => "#607D8B",  // Blue Grey
            _ => "#999999"  // Default grey
        };
    }
}
