using FolderFreshLite.Models;
using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Conditions;

/// <summary>
/// Tests for Kind condition (file type matching)
/// </summary>
public class KindConditionTests : IDisposable
{
    private readonly TestFileHelper _helper;
    private readonly RuleService _ruleService;

    public KindConditionTests()
    {
        _helper = new TestFileHelper();
        _ruleService = new RuleService();
    }

    public void Dispose() => _helper.Dispose();

    [Theory]
    // Images
    [InlineData("photo.jpg", "Image", true)]
    [InlineData("photo.jpeg", "Image", true)]
    [InlineData("photo.png", "Image", true)]
    [InlineData("photo.gif", "Image", true)]
    [InlineData("photo.bmp", "Image", true)]
    [InlineData("photo.svg", "Image", true)]
    [InlineData("photo.webp", "Image", true)]
    [InlineData("photo.ico", "Image", true)]
    [InlineData("photo.tiff", "Image", true)]
    // Documents
    [InlineData("report.doc", "Document", true)]
    [InlineData("report.docx", "Document", true)]
    [InlineData("report.rtf", "Document", true)]
    [InlineData("report.odt", "Document", true)]
    // PDF
    [InlineData("manual.pdf", "PDF", true)]
    // Video
    [InlineData("movie.mp4", "Video", true)]
    [InlineData("movie.avi", "Video", true)]
    [InlineData("movie.mkv", "Video", true)]
    [InlineData("movie.mov", "Video", true)]
    [InlineData("movie.wmv", "Video", true)]
    [InlineData("movie.flv", "Video", true)]
    [InlineData("movie.webm", "Video", true)]
    // Audio
    [InlineData("song.mp3", "Audio", true)]
    [InlineData("song.wav", "Audio", true)]
    [InlineData("song.flac", "Audio", true)]
    [InlineData("song.aac", "Audio", true)]
    [InlineData("song.ogg", "Audio", true)]
    [InlineData("song.m4a", "Audio", true)]
    [InlineData("song.wma", "Audio", true)]
    // Archive
    [InlineData("backup.zip", "Archive", true)]
    [InlineData("backup.rar", "Archive", true)]
    [InlineData("backup.7z", "Archive", true)]
    [InlineData("backup.tar", "Archive", true)]
    [InlineData("backup.gz", "Archive", true)]
    [InlineData("backup.bz2", "Archive", true)]
    // Executable
    [InlineData("setup.exe", "Executable", true)]
    [InlineData("installer.msi", "Executable", true)]
    [InlineData("script.bat", "Executable", true)]
    [InlineData("script.cmd", "Executable", true)]
    [InlineData("script.ps1", "Executable", true)]
    // Code
    [InlineData("program.cs", "Code", true)]
    [InlineData("script.js", "Code", true)]
    [InlineData("app.ts", "Code", true)]
    [InlineData("main.py", "Code", true)]
    [InlineData("Main.java", "Code", true)]
    [InlineData("program.cpp", "Code", true)]
    [InlineData("header.h", "Code", true)]
    [InlineData("page.html", "Code", true)]
    [InlineData("style.css", "Code", true)]
    [InlineData("config.json", "Code", true)]
    [InlineData("data.xml", "Code", true)]
    // Text
    [InlineData("notes.txt", "Text", true)]
    [InlineData("readme.md", "Text", true)]
    [InlineData("debug.log", "Text", true)]
    // Spreadsheet
    [InlineData("data.xls", "Spreadsheet", true)]
    [InlineData("data.xlsx", "Spreadsheet", true)]
    [InlineData("data.csv", "Spreadsheet", true)]
    [InlineData("data.ods", "Spreadsheet", true)]
    // Presentation
    [InlineData("slides.ppt", "Presentation", true)]
    [InlineData("slides.pptx", "Presentation", true)]
    [InlineData("slides.odp", "Presentation", true)]
    // Font
    [InlineData("arial.ttf", "Font", true)]
    [InlineData("roboto.otf", "Font", true)]
    [InlineData("icon.woff", "Font", true)]
    [InlineData("icon.woff2", "Font", true)]
    // Other (unknown extensions)
    [InlineData("file.xyz", "Other", true)]
    [InlineData("file.unknown", "Other", true)]
    public void Kind_Is_MatchesCorrectFileType(string fileName, string expectedKind, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Kind,
            Operator = ConditionOperator.Is,
            Value = expectedKind
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("photo.jpg", "image", true)]  // lowercase
    [InlineData("photo.jpg", "IMAGE", true)]  // uppercase
    [InlineData("photo.jpg", "Image", true)]  // mixed
    public void Kind_Is_CaseInsensitive(string fileName, string kindValue, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Kind,
            Operator = ConditionOperator.Is,
            Value = kindValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("photo.jpg", "Video", true)]
    [InlineData("photo.jpg", "Image", false)]
    [InlineData("movie.mp4", "Audio", true)]
    [InlineData("movie.mp4", "Video", false)]
    public void Kind_IsNot_Works(string fileName, string kindValue, bool expected)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Kind,
            Operator = ConditionOperator.IsNot,
            Value = kindValue
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("photo.JPG", "Image")]  // uppercase extension
    [InlineData("photo.Jpg", "Image")]  // mixed case extension
    public void Kind_ExtensionCaseInsensitive(string fileName, string expectedKind)
    {
        var file = _helper.CreateFile(fileName);
        var condition = new Condition
        {
            Attribute = ConditionAttribute.Kind,
            Operator = ConditionOperator.Is,
            Value = expectedKind
        };

        var result = _ruleService.EvaluateCondition(condition, file);

        Assert.True(result);
    }
}
