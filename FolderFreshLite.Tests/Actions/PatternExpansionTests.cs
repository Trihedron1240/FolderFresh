using FolderFreshLite.Services;
using FolderFreshLite.Tests.Helpers;

namespace FolderFreshLite.Tests.Actions;

/// <summary>
/// Tests for pattern expansion in rename and subfolder actions.
/// Validates all supported tokens: {Name}, {Extension}, {Date}, {Kind}, etc.
/// </summary>
public class PatternExpansionTests : IDisposable
{
    private readonly TestFileHelper _helper;

    public PatternExpansionTests()
    {
        _helper = new TestFileHelper();
    }

    public void Dispose() => _helper.Dispose();

    #region Name Tokens

    [Theory]
    [InlineData("document.pdf", "{Name}", "document")]
    [InlineData("my_file.txt", "{Name}", "my_file")]
    [InlineData("UPPERCASE.PDF", "{Name}", "UPPERCASE")]
    [InlineData("file.with.dots.pdf", "{Name}", "file.with.dots")]
    public void Name_Token_ExtractsNameWithoutExtension(string fileName, string pattern, string expected)
    {
        var file = _helper.CreateFile(fileName);

        var result = RuleService.ExpandPattern(pattern, file);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void Name_LowercaseToken_Works()
    {
        var file = _helper.CreateFile("Document.pdf");

        var result = RuleService.ExpandPattern("{name}", file);

        Assert.Equal("Document", result);  // Same as {Name}
    }

    #endregion

    #region Extension Tokens

    [Theory]
    [InlineData("document.pdf", "{Extension}", "pdf")]
    [InlineData("image.PNG", "{Extension}", "PNG")]
    [InlineData("file.tar.gz", "{Extension}", "gz")]
    public void Extension_Token_ExtractsWithoutDot(string fileName, string pattern, string expected)
    {
        var file = _helper.CreateFile(fileName);

        var result = RuleService.ExpandPattern(pattern, file);

        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("{extension}")]
    [InlineData("{ext}")]
    public void Extension_AlternativeTokens_Work(string pattern)
    {
        var file = _helper.CreateFile("document.pdf");

        var result = RuleService.ExpandPattern(pattern, file);

        Assert.Equal("pdf", result);
    }

    #endregion

    #region Date Tokens (Modified Date)

    [Fact]
    public void Date_DefaultFormat()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern("{Date}", file);

        Assert.Equal("2024-06-15", result);
    }

    [Fact]
    public void Date_LowercaseToken()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern("{date}", file);

        Assert.Equal("2024-06-15", result);
    }

    [Theory]
    [InlineData("{date:yyyy}", "2024")]
    [InlineData("{date:MM}", "06")]
    [InlineData("{date:dd}", "15")]
    [InlineData("{date:yyyy-MM}", "2024-06")]
    [InlineData("{date:yyyyMMdd}", "20240615")]
    [InlineData("{date:MMMM}", "June")]
    [InlineData("{date:MMM}", "Jun")]
    public void Date_CustomFormat(string pattern, string expected)
    {
        var file = _helper.CreateFileWithDates("doc.pdf", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern(pattern, file);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void Year_Token()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern("{Year}", file);

        Assert.Equal("2024", result);
    }

    [Fact]
    public void Month_Token_ZeroPadded()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern("{Month}", file);

        Assert.Equal("06", result);
    }

    [Fact]
    public void Day_Token_ZeroPadded()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", modifiedDate: new DateTime(2024, 6, 5));

        var result = RuleService.ExpandPattern("{Day}", file);

        Assert.Equal("05", result);
    }

    [Fact]
    public void YearMonthDay_LowercaseTokens()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", modifiedDate: new DateTime(2024, 6, 15));

        var yearResult = RuleService.ExpandPattern("{year}", file);
        var monthResult = RuleService.ExpandPattern("{month}", file);
        var dayResult = RuleService.ExpandPattern("{day}", file);

        Assert.Equal("2024", yearResult);
        Assert.Equal("06", monthResult);
        Assert.Equal("15", dayResult);
    }

    #endregion

    #region Created Date Tokens

    [Fact]
    public void Created_CustomFormat()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", createdDate: new DateTime(2023, 3, 20));

        var result = RuleService.ExpandPattern("{created:yyyy-MM-dd}", file);

        Assert.Equal("2023-03-20", result);
    }

    [Fact]
    public void CreatedYear_Token()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", createdDate: new DateTime(2023, 3, 20));

        var result = RuleService.ExpandPattern("{CreatedYear}", file);

        Assert.Equal("2023", result);
    }

    [Fact]
    public void CreatedMonth_Token()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", createdDate: new DateTime(2023, 3, 20));

        var result = RuleService.ExpandPattern("{CreatedMonth}", file);

        Assert.Equal("03", result);
    }

    [Fact]
    public void CreatedDay_Token()
    {
        var file = _helper.CreateFileWithDates("doc.pdf", createdDate: new DateTime(2023, 3, 20));

        var result = RuleService.ExpandPattern("{CreatedDay}", file);

        Assert.Equal("20", result);
    }

    #endregion

    #region Today Tokens

    [Fact]
    public void Today_DefaultFormat()
    {
        var file = _helper.CreateFile("doc.pdf");
        var today = DateTime.Now.ToString("yyyy-MM-dd");

        var result = RuleService.ExpandPattern("{Today}", file);

        Assert.Equal(today, result);
    }

    [Fact]
    public void Today_CustomFormat()
    {
        var file = _helper.CreateFile("doc.pdf");
        var expected = DateTime.Now.ToString("yyyyMMdd");

        var result = RuleService.ExpandPattern("{today:yyyyMMdd}", file);

        Assert.Equal(expected, result);
    }

    #endregion

    #region Kind Token

    [Theory]
    [InlineData("photo.jpg", "Image")]
    [InlineData("document.pdf", "PDF")]
    [InlineData("report.docx", "Document")]
    [InlineData("movie.mp4", "Video")]
    [InlineData("song.mp3", "Audio")]
    [InlineData("backup.zip", "Archive")]
    [InlineData("setup.exe", "Executable")]
    [InlineData("script.js", "Code")]
    [InlineData("readme.txt", "Text")]
    [InlineData("data.xlsx", "Spreadsheet")]
    [InlineData("slides.pptx", "Presentation")]
    [InlineData("font.ttf", "Font")]
    [InlineData("unknown.xyz", "Other")]
    public void Kind_Token_ReturnsFileKind(string fileName, string expectedKind)
    {
        var file = _helper.CreateFile(fileName);

        var result = RuleService.ExpandPattern("{Kind}", file);

        Assert.Equal(expectedKind, result);
    }

    [Fact]
    public void Kind_LowercaseToken()
    {
        var file = _helper.CreateFile("photo.jpg");

        var result = RuleService.ExpandPattern("{kind}", file);

        Assert.Equal("Image", result);  // Same as {Kind}
    }

    #endregion

    #region Combined Patterns

    [Fact]
    public void CombinedPattern_NameAndExtension()
    {
        var file = _helper.CreateFile("document.pdf");

        var result = RuleService.ExpandPattern("{Name}.{Extension}", file);

        Assert.Equal("document.pdf", result);
    }

    [Fact]
    public void CombinedPattern_DateAndName()
    {
        var file = _helper.CreateFileWithDates("report.pdf", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern("{Date}_{Name}.{ext}", file);

        Assert.Equal("2024-06-15_report.pdf", result);
    }

    [Fact]
    public void CombinedPattern_KindOrganization()
    {
        var file = _helper.CreateFileWithDates("photo.jpg", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern("{Kind}/{Year}/{Month}/{Name}.{ext}", file);

        Assert.Equal("Image/2024/06/photo.jpg", result);
    }

    [Fact]
    public void CombinedPattern_BackupNaming()
    {
        var file = _helper.CreateFileWithDates("important.docx", modifiedDate: new DateTime(2024, 6, 15));

        var result = RuleService.ExpandPattern("backup_{Name}_{date:yyyyMMdd}.{ext}", file);

        Assert.Equal("backup_important_20240615.docx", result);
    }

    [Fact]
    public void CombinedPattern_ArchiveStructure()
    {
        var file = _helper.CreateFileWithDates("quarterly_report.xlsx",
            modifiedDate: new DateTime(2024, 6, 15),
            createdDate: new DateTime(2024, 3, 1));

        var result = RuleService.ExpandPattern("Archives/{CreatedYear}/Q{created:MM}/{Name}.{ext}", file);

        Assert.Equal("Archives/2024/Q03/quarterly_report.xlsx", result);
    }

    #endregion

    #region Edge Cases

    [Fact]
    public void Pattern_NoTokens_ReturnsAsIs()
    {
        var file = _helper.CreateFile("document.pdf");

        var result = RuleService.ExpandPattern("static_name.txt", file);

        Assert.Equal("static_name.txt", result);
    }

    [Fact]
    public void Pattern_MultipleOfSameToken()
    {
        var file = _helper.CreateFile("document.pdf");

        var result = RuleService.ExpandPattern("{Name}_{Name}.{ext}", file);

        Assert.Equal("document_document.pdf", result);
    }

    [Fact]
    public void Pattern_UnknownToken_RemainsUnchanged()
    {
        var file = _helper.CreateFile("document.pdf");

        var result = RuleService.ExpandPattern("{Unknown}.pdf", file);

        Assert.Equal("{Unknown}.pdf", result);  // Unknown tokens are not expanded
    }

    [Fact]
    public void Pattern_EmptyString()
    {
        var file = _helper.CreateFile("document.pdf");

        var result = RuleService.ExpandPattern("", file);

        Assert.Equal("", result);
    }

    [Fact]
    public void Pattern_FileWithNoExtension()
    {
        var file = _helper.CreateFile("Makefile");  // No extension

        var nameResult = RuleService.ExpandPattern("{Name}", file);
        var extResult = RuleService.ExpandPattern("{Extension}", file);

        Assert.Equal("Makefile", nameResult);
        Assert.Equal("", extResult);
    }

    [Fact]
    public void Pattern_CaseSensitivity()
    {
        var file = _helper.CreateFile("Document.PDF");

        var nameUpper = RuleService.ExpandPattern("{Name}", file);
        var nameLower = RuleService.ExpandPattern("{name}", file);
        var extUpper = RuleService.ExpandPattern("{Extension}", file);
        var extLower = RuleService.ExpandPattern("{extension}", file);

        // All should return the same value (from file)
        Assert.Equal("Document", nameUpper);
        Assert.Equal("Document", nameLower);
        Assert.Equal("PDF", extUpper);
        Assert.Equal("PDF", extLower);
    }

    #endregion
}
