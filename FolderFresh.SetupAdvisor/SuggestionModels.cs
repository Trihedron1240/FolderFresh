namespace FolderFresh.SetupAdvisor;

public sealed class FolderAnalysisOptions
{
    public string SourcePath { get; set; } = string.Empty;
    public bool Recursive { get; set; }
    public int MaxFiles { get; set; } = 500;
}

public sealed class SetupAnalysisResult
{
    public string SourcePath { get; set; } = string.Empty;
    public int FilesScanned { get; set; }
    public List<SuggestedCategory> Categories { get; set; } = new();
    public List<SuggestedRule> Rules { get; set; } = new();
}

public sealed class SuggestedCategory
{
    public string Key { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Destination { get; set; } = string.Empty;
    public string Icon { get; set; } = string.Empty;
    public string Color { get; set; } = string.Empty;
    public List<string> Extensions { get; set; } = new();
    public string Reason { get; set; } = string.Empty;
    public int FileCount { get; set; }
    public List<string> SampleFiles { get; set; } = new();
}

public sealed class SuggestedRule
{
    public string Key { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string MatchToken { get; set; } = string.Empty;
    public string TargetCategoryKey { get; set; } = string.Empty;
    public string Reason { get; set; } = string.Empty;
    public int MatchCount { get; set; }
    public List<string> SampleFiles { get; set; } = new();
}
