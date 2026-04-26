using System.Text.RegularExpressions;

namespace FolderFresh.SetupAdvisor;

public sealed class SetupAdvisorService
{
    private static readonly HashSet<string> StopWords = new(StringComparer.OrdinalIgnoreCase)
    {
        "a", "an", "and", "archive", "attachment", "backup", "copy", "document", "draft",
        "exported", "file", "files", "final", "img", "image", "new", "notes", "scan",
        "temp", "test", "untitled", "version", "v1", "v2", "v3", "the"
    };

    private static readonly HashSet<string> ReservedProjectTokens = new(StringComparer.OrdinalIgnoreCase)
    {
        "assignment", "backup", "bill", "capture", "cover", "coverletter", "cv", "dump",
        "expense", "expenses", "export", "homework", "install", "installer", "invoice",
        "lecture", "portfolio", "receipt", "report", "resume", "screen", "screenshot",
        "setup", "statement", "support", "syllabus", "tax", "taxes"
    };

    public Task<SetupAnalysisResult> AnalyzeAsync(FolderAnalysisOptions options, CancellationToken cancellationToken = default)
    {
        return Task.Run(() => Analyze(options), cancellationToken);
    }

    public SetupAnalysisResult Analyze(FolderAnalysisOptions options)
    {
        if (!Directory.Exists(options.SourcePath))
        {
            throw new DirectoryNotFoundException($"Source folder not found: {options.SourcePath}");
        }

        var records = EnumerateFiles(options).ToList();
        var suggestions = new List<CategoryRuleSuggestion>();
        var usedPaths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var existingCategoryKeys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        AddKnownIntentSuggestions(records, suggestions, usedPaths, existingCategoryKeys);
        AddProjectSuggestions(records, suggestions, usedPaths, existingCategoryKeys);

        var orderedSuggestions = suggestions
            .OrderByDescending(s => s.Files.Count)
            .ThenBy(s => s.Category.Name)
            .ToList();

        return new SetupAnalysisResult
        {
            SourcePath = options.SourcePath,
            FilesScanned = records.Count,
            Categories = orderedSuggestions
                .Select(s => new SuggestedCategory
                {
                    Key = s.Category.Key,
                    Name = s.Category.Name,
                    Destination = s.Category.Destination,
                    Icon = s.Category.Icon,
                    Color = s.Category.Color,
                    Extensions = s.Category.Extensions.ToList(),
                    Reason = s.Reason,
                    FileCount = s.Files.Count,
                    SampleFiles = s.Files.Take(5).Select(f => f.FileName).ToList()
                })
                .ToList(),
            Rules = orderedSuggestions
                .Select((s, index) => new SuggestedRule
                {
                    Key = $"{s.Category.Key}-rule-{index}",
                    Name = $"Move {s.Category.Name} files",
                    MatchToken = s.RuleToken,
                    TargetCategoryKey = s.Category.Key,
                    Reason = s.Reason,
                    MatchCount = s.Files.Count,
                    SampleFiles = s.Files.Take(5).Select(f => f.FileName).ToList()
                })
                .ToList()
        };
    }

    private static IEnumerable<FileRecord> EnumerateFiles(FolderAnalysisOptions options)
    {
        var searchOption = options.Recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;

        return Directory
            .EnumerateFiles(options.SourcePath, "*", searchOption)
            .Take(options.MaxFiles)
            .Select(path => new FileInfo(path))
            .Where(file => file.Exists)
            .Select(file => new FileRecord(
                file.FullName,
                file.Name,
                Path.GetFileNameWithoutExtension(file.Name),
                file.Extension.ToLowerInvariant(),
                TokenizeFileName(file.Name)));
    }

    private static IReadOnlyList<string> TokenizeFileName(string fileName)
    {
        var stem = Path.GetFileNameWithoutExtension(fileName);
        var spaced = Regex.Replace(stem, "([a-z])([A-Z])", "$1 $2");
        return Regex
            .Split(spaced.ToLowerInvariant(), @"[^a-z0-9]+")
            .Where(token => !string.IsNullOrWhiteSpace(token))
            .ToList();
    }

    private static void AddKnownIntentSuggestions(
        List<FileRecord> records,
        List<CategoryRuleSuggestion> suggestions,
        HashSet<string> usedPaths,
        HashSet<string> existingCategoryKeys)
    {
        AddKnownIntentSuggestion(
            records,
            suggestions,
            usedPaths,
            existingCategoryKeys,
            new KnownIntent(
                "screenshots",
                "Screenshots",
                "Screenshots",
                "\U0001F5BC",
                "#8B5CF6",
                "Suggested because these image files match common screenshot naming patterns.",
                file => IsImage(file.Extension) && HasAnyToken(file, "screenshot", "screen", "capture", "snip")),
            minFiles: 3);

        AddKnownIntentSuggestion(
            records,
            suggestions,
            usedPaths,
            existingCategoryKeys,
            new KnownIntent(
                "installers",
                "Installers",
                "Installers",
                "\U0001F4E6",
                "#14B8A6",
                "Suggested because these files look like installers or setup packages.",
                file => IsExecutable(file.Extension) || HasAnyToken(file, "installer", "install", "setup")),
            minFiles: 2);

        AddKnownIntentSuggestion(
            records,
            suggestions,
            usedPaths,
            existingCategoryKeys,
            new KnownIntent(
                "finance",
                "Finance",
                "Finance",
                "\U0001F4B0",
                "#10B981",
                "Suggested because several documents share finance-related terms like invoice, receipt, statement, or tax.",
                file => IsDocumentLike(file.Extension) && HasAnyToken(file, "invoice", "receipt", "statement", "bill", "tax", "budget", "expense", "expenses", "payroll")),
            minFiles: 2);

        AddKnownIntentSuggestion(
            records,
            suggestions,
            usedPaths,
            existingCategoryKeys,
            new KnownIntent(
                "job-applications",
                "Job Applications",
                "Job Applications",
                "\U0001F4BC",
                "#F59E0B",
                "Suggested because these files look like resumes, CVs, cover letters, or related application documents.",
                file => IsDocumentLike(file.Extension) && HasAnyToken(file, "resume", "cv", "coverletter", "cover", "portfolio")),
            minFiles: 2);

        AddKnownIntentSuggestion(
            records,
            suggestions,
            usedPaths,
            existingCategoryKeys,
            new KnownIntent(
                "school",
                "School",
                "School",
                "\U0001F393",
                "#3B82F6",
                "Suggested because these files look like coursework, lectures, or assignments.",
                file => IsDocumentLike(file.Extension) && HasAnyToken(file, "lecture", "assignment", "coursework", "syllabus", "homework")),
            minFiles: 2);

        AddKnownIntentSuggestion(
            records,
            suggestions,
            usedPaths,
            existingCategoryKeys,
            new KnownIntent(
                "support-files",
                "Support Files",
                "Support Files",
                "\U0001F6E0",
                "#6366F1",
                "Suggested because several files share support-oriented naming and could live together.",
                file => HasAnyToken(file, "support", "appendix", "attachment")),
            minFiles: 2);

        AddKnownIntentSuggestion(
            records,
            suggestions,
            usedPaths,
            existingCategoryKeys,
            new KnownIntent(
                "exports",
                "Exports",
                "Exports",
                "\U0001F4CA",
                "#EC4899",
                "Suggested because these files look like exported reports, dumps, or generated extracts.",
                file => HasAnyToken(file, "export", "dump", "extract", "report", "backup")),
            minFiles: 2);
    }

    private static void AddKnownIntentSuggestion(
        List<FileRecord> records,
        List<CategoryRuleSuggestion> suggestions,
        HashSet<string> usedPaths,
        HashSet<string> existingCategoryKeys,
        KnownIntent intent,
        int minFiles)
    {
        var matches = records
            .Where(file => !usedPaths.Contains(file.FullPath))
            .Where(intent.Matcher)
            .ToList();

        if (matches.Count < minFiles)
        {
            return;
        }

        var category = new SuggestedCategoryDefinition
        {
            Key = MakeUniqueKey(intent.Id, existingCategoryKeys),
            Name = intent.Name,
            Destination = intent.Destination,
            Icon = intent.Icon,
            Color = intent.Color,
            Extensions = matches
                .Select(file => file.Extension)
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .OrderBy(ext => ext)
                .ToList()
        };

        suggestions.Add(new CategoryRuleSuggestion(category, matches, intent.Reason, PickRuleToken(matches, intent.Id)));
        foreach (var path in matches.Select(file => file.FullPath))
        {
            usedPaths.Add(path);
        }
    }

    private static void AddProjectSuggestions(
        List<FileRecord> records,
        List<CategoryRuleSuggestion> suggestions,
        HashSet<string> usedPaths,
        HashSet<string> existingCategoryKeys)
    {
        var tokenFrequencies = records
            .Where(file => !usedPaths.Contains(file.FullPath))
            .SelectMany(file => file.Tokens.Distinct(StringComparer.OrdinalIgnoreCase))
            .Where(IsProjectCandidateToken)
            .GroupBy(token => token, StringComparer.OrdinalIgnoreCase)
            .Select(group => new { Token = group.Key, Count = group.Count() })
            .Where(group => group.Count >= 3)
            .OrderByDescending(group => group.Count)
            .ThenBy(group => group.Token)
            .ToList();

        foreach (var candidate in tokenFrequencies)
        {
            var matches = records
                .Where(file => !usedPaths.Contains(file.FullPath))
                .Where(file => file.Tokens.Contains(candidate.Token, StringComparer.OrdinalIgnoreCase))
                .ToList();

            if (matches.Count < 3)
            {
                continue;
            }

            var commonStem = GetCommonStem(matches.Select(file => file.NameWithoutExtension).ToList());
            var projectSeed = !string.IsNullOrWhiteSpace(commonStem) ? commonStem : candidate.Token;
            var projectName = ToDisplayName(projectSeed);
            var category = new SuggestedCategoryDefinition
            {
                Key = MakeUniqueKey(projectSeed, existingCategoryKeys),
                Name = projectName,
                Destination = Path.Combine("Projects", projectName),
                Icon = "\U0001F4C1",
                Color = "#6366F1",
                Extensions = matches
                    .Select(file => file.Extension)
                    .Distinct(StringComparer.OrdinalIgnoreCase)
                    .OrderBy(ext => ext)
                    .ToList()
            };

            suggestions.Add(new CategoryRuleSuggestion(
                category,
                matches,
                $"Suggested because {matches.Count} files share the token \"{candidate.Token}\" and look like a cohesive project cluster.",
                NormalizeRuleToken(projectSeed)));

            foreach (var path in matches.Select(file => file.FullPath))
            {
                usedPaths.Add(path);
            }
        }
    }

    private static bool IsProjectCandidateToken(string token)
    {
        if (string.IsNullOrWhiteSpace(token) || token.Length < 4)
        {
            return false;
        }

        if (StopWords.Contains(token) || ReservedProjectTokens.Contains(token))
        {
            return false;
        }

        return token.Any(char.IsLetter) && !token.All(char.IsDigit);
    }

    private static string PickRuleToken(List<FileRecord> matches, string fallback)
    {
        var bestToken = matches
            .SelectMany(file => file.Tokens.Distinct(StringComparer.OrdinalIgnoreCase))
            .Where(token => !StopWords.Contains(token))
            .GroupBy(token => token, StringComparer.OrdinalIgnoreCase)
            .OrderByDescending(group => group.Count())
            .ThenByDescending(group => group.Key.Length)
            .Select(group => group.Key)
            .FirstOrDefault();

        return bestToken ?? fallback;
    }

    private static bool HasAnyToken(FileRecord file, params string[] values)
    {
        return values.Any(value => file.Tokens.Contains(value, StringComparer.OrdinalIgnoreCase));
    }

    private static bool IsDocumentLike(string extension)
    {
        return extension is ".pdf" or ".doc" or ".docx" or ".txt" or ".rtf" or ".md" or ".xls" or ".xlsx" or ".csv" or ".ppt" or ".pptx" or ".odt" or ".ods" or ".odp";
    }

    private static bool IsExecutable(string extension)
    {
        return extension is ".exe" or ".msi" or ".msix" or ".bat" or ".cmd";
    }

    private static bool IsImage(string extension)
    {
        return extension is ".jpg" or ".jpeg" or ".png" or ".gif" or ".bmp" or ".webp" or ".tiff";
    }

    private static string MakeUniqueKey(string baseValue, HashSet<string> existingKeys)
    {
        var slug = Regex.Replace(baseValue.ToLowerInvariant(), @"[^a-z0-9]+", "-").Trim('-');
        if (string.IsNullOrWhiteSpace(slug))
        {
            slug = "suggested";
        }

        var candidate = slug;
        var suffix = 2;
        while (!existingKeys.Add(candidate))
        {
            candidate = $"{slug}-{suffix}";
            suffix++;
        }

        return candidate;
    }

    private static string ToDisplayName(string token)
    {
        return string.Join(" ",
            Regex.Replace(token.Replace("_", " ").Replace("-", " "), "([a-z])([A-Z])", "$1 $2")
                .Split('-', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .SelectMany(part => part.Split(' ', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
                .Select(part => char.ToUpperInvariant(part[0]) + part[1..]));
    }

    private static string NormalizeRuleToken(string value)
    {
        return Regex.Replace(value.ToLowerInvariant(), @"[^a-z0-9]+", string.Empty);
    }

    private static string? GetCommonStem(List<string> names)
    {
        if (names.Count == 0)
        {
            return null;
        }

        var prefix = names[0];
        foreach (var name in names.Skip(1))
        {
            var maxLength = Math.Min(prefix.Length, name.Length);
            var index = 0;
            while (index < maxLength && char.ToLowerInvariant(prefix[index]) == char.ToLowerInvariant(name[index]))
            {
                index++;
            }

            prefix = prefix[..index];
            if (prefix.Length == 0)
            {
                return null;
            }
        }

        prefix = prefix.Trim('_', '-', ' ');
        return prefix.Length >= 4 ? prefix : null;
    }

    private sealed record FileRecord(
        string FullPath,
        string FileName,
        string NameWithoutExtension,
        string Extension,
        IReadOnlyList<string> Tokens);

    private sealed record KnownIntent(
        string Id,
        string Name,
        string Destination,
        string Icon,
        string Color,
        string Reason,
        Func<FileRecord, bool> Matcher);

    private sealed record CategoryRuleSuggestion(
        SuggestedCategoryDefinition Category,
        List<FileRecord> Files,
        string Reason,
        string RuleToken);

    private sealed class SuggestedCategoryDefinition
    {
        public string Key { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Destination { get; set; } = string.Empty;
        public string Icon { get; set; } = string.Empty;
        public string Color { get; set; } = string.Empty;
        public List<string> Extensions { get; set; } = new();
    }
}
