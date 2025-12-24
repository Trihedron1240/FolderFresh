using System;
using System.IO;

namespace FolderFreshLite.Tests.Helpers;

/// <summary>
/// Helper class for creating test files with specific properties
/// </summary>
public class TestFileHelper : IDisposable
{
    private readonly string _testDirectory;
    private readonly List<string> _createdFiles = new();
    private readonly List<string> _createdDirectories = new();

    public string TestDirectory => _testDirectory;

    public TestFileHelper()
    {
        _testDirectory = Path.Combine(Path.GetTempPath(), "FolderFreshTests_" + Guid.NewGuid().ToString("N")[..8]);
        Directory.CreateDirectory(_testDirectory);
        _createdDirectories.Add(_testDirectory);
    }

    /// <summary>
    /// Creates a test file with the specified name and optional content
    /// </summary>
    public FileInfo CreateFile(string fileName, string? content = null, long? sizeInBytes = null)
    {
        var filePath = Path.Combine(_testDirectory, fileName);
        var directory = Path.GetDirectoryName(filePath);

        if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
        {
            Directory.CreateDirectory(directory);
            _createdDirectories.Add(directory);
        }

        if (sizeInBytes.HasValue)
        {
            // Create file with specific size
            using var fs = File.Create(filePath);
            fs.SetLength(sizeInBytes.Value);
        }
        else
        {
            File.WriteAllText(filePath, content ?? "test content");
        }

        _createdFiles.Add(filePath);
        return new FileInfo(filePath);
    }

    /// <summary>
    /// Creates a test file with specific dates and optionally specific size
    /// </summary>
    public FileInfo CreateFileWithDates(
        string fileName,
        DateTime? createdDate = null,
        DateTime? modifiedDate = null,
        DateTime? accessedDate = null,
        long? sizeInBytes = null)
    {
        var file = CreateFile(fileName, sizeInBytes: sizeInBytes);

        if (createdDate.HasValue)
            File.SetCreationTime(file.FullName, createdDate.Value);

        if (modifiedDate.HasValue)
            File.SetLastWriteTime(file.FullName, modifiedDate.Value);

        if (accessedDate.HasValue)
            File.SetLastAccessTime(file.FullName, accessedDate.Value);

        file.Refresh();
        return file;
    }

    /// <summary>
    /// Creates a subdirectory in the test folder
    /// </summary>
    public string CreateSubdirectory(string name)
    {
        var path = Path.Combine(_testDirectory, name);
        Directory.CreateDirectory(path);
        _createdDirectories.Add(path);
        return path;
    }

    /// <summary>
    /// Gets all files currently in the test directory (recursive)
    /// </summary>
    public List<string> GetAllFiles()
    {
        return Directory.GetFiles(_testDirectory, "*", SearchOption.AllDirectories).ToList();
    }

    /// <summary>
    /// Gets the final folder state as a dictionary of relative paths
    /// </summary>
    public Dictionary<string, string> GetFolderState()
    {
        var state = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        foreach (var file in Directory.GetFiles(_testDirectory, "*", SearchOption.AllDirectories))
        {
            var relativePath = Path.GetRelativePath(_testDirectory, file);
            var fileName = Path.GetFileName(file);
            state[fileName] = relativePath;
        }

        return state;
    }

    /// <summary>
    /// Checks if a file exists at the given relative path
    /// </summary>
    public bool FileExistsAt(string relativePath)
    {
        var fullPath = Path.Combine(_testDirectory, relativePath);
        return File.Exists(fullPath);
    }

    public void Dispose()
    {
        // Clean up in reverse order (files first, then directories)
        foreach (var file in _createdFiles)
        {
            try { if (File.Exists(file)) File.Delete(file); } catch { }
        }

        // Delete directories from deepest to shallowest
        foreach (var dir in _createdDirectories.OrderByDescending(d => d.Length))
        {
            try { if (Directory.Exists(dir)) Directory.Delete(dir, true); } catch { }
        }
    }
}
