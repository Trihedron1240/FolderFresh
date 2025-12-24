using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using FolderFresh.Components;
using FolderFresh.Models;

namespace FolderFresh.Services;

/// <summary>
/// Executes file organization operations with progress reporting, error handling, and undo support.
/// </summary>
public class OrganizationExecutor
{
    private readonly RuleService _ruleService;
    private readonly CategoryService _categoryService;
    private readonly ConcurrentDictionary<string, OrganizationUndoState> _undoStates = new();

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    public OrganizationExecutor(RuleService ruleService, CategoryService categoryService)
    {
        _ruleService = ruleService;
        _categoryService = categoryService;
    }

    /// <summary>
    /// Executes organization for a list of files based on their organize results.
    /// </summary>
    /// <param name="folder">The watched folder being organized.</param>
    /// <param name="filesToOrganize">Files with their organization destinations.</param>
    /// <param name="basePath">Base path for relative destination resolution.</param>
    /// <param name="settings">App settings for conflict resolution etc.</param>
    /// <param name="progress">Optional progress reporter.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Detailed organization result.</returns>
    public async Task<DetailedOrganizationResult> ExecuteOrganizationAsync(
        WatchedFolder folder,
        List<FileOrganizeResult> filesToOrganize,
        string basePath,
        AppSettings settings,
        IProgress<OrganizationProgress>? progress = null,
        CancellationToken cancellationToken = default)
    {
        var result = new DetailedOrganizationResult
        {
            FolderId = folder.Id,
            FolderPath = folder.FolderPath,
            StartTime = DateTime.Now
        };

        var stopwatch = Stopwatch.StartNew();
        var undoOperations = new List<MoveOperation>();
        var totalFiles = filesToOrganize.Count;
        var processedCount = 0;

        foreach (var fileResult in filesToOrganize)
        {
            if (cancellationToken.IsCancellationRequested)
            {
                result.WasCancelled = true;
                break;
            }

            processedCount++;
            var fileName = Path.GetFileName(fileResult.SourcePath);

            progress?.Report(new OrganizationProgress
            {
                CurrentFile = processedCount,
                TotalFiles = totalFiles,
                CurrentFileName = fileName,
                CurrentAction = "Organizing"
            });

            try
            {
                // Check file still exists
                if (!File.Exists(fileResult.SourcePath))
                {
                    result.Errors.Add((fileResult.SourcePath, "File no longer exists"));
                    result.FilesSkipped++;
                    continue;
                }

                // Check file is not locked
                if (IsFileLocked(fileResult.SourcePath))
                {
                    result.Errors.Add((fileResult.SourcePath, "File is in use by another process"));
                    result.FilesSkipped++;
                    continue;
                }

                // Execute based on match type
                if (fileResult.MatchedBy == OrganizeMatchType.Rule)
                {
                    var moveOps = await ExecuteRuleActionsAsync(fileResult, basePath, settings);
                    undoOperations.AddRange(moveOps);

                    if (moveOps.Any(m => m.ActionType == "move"))
                        result.FilesMoved++;
                    if (moveOps.Any(m => m.ActionType == "copy"))
                        result.FilesCopied++;
                    if (moveOps.Any(m => m.ActionType == "delete"))
                        result.FilesDeleted++;
                }
                else if (fileResult.MatchedBy == OrganizeMatchType.Category)
                {
                    var moveOp = await ExecuteCategoryMoveAsync(fileResult, basePath, settings);
                    if (moveOp != null)
                    {
                        undoOperations.Add(moveOp);
                        result.FilesMoved++;
                    }
                }
                else
                {
                    result.FilesSkipped++;
                }

                result.FilesProcessed++;
            }
            catch (UnauthorizedAccessException)
            {
                result.Errors.Add((fileResult.SourcePath, "Access denied"));
                result.FilesSkipped++;
            }
            catch (PathTooLongException)
            {
                result.Errors.Add((fileResult.SourcePath, "Path too long"));
                result.FilesSkipped++;
            }
            catch (IOException ex)
            {
                result.Errors.Add((fileResult.SourcePath, ex.Message));
                result.FilesSkipped++;
            }
            catch (Exception ex)
            {
                result.Errors.Add((fileResult.SourcePath, $"Unexpected error: {ex.Message}"));
                result.FilesSkipped++;
            }
        }

        stopwatch.Stop();
        result.Duration = stopwatch.Elapsed;
        result.EndTime = DateTime.Now;
        result.MoveOperations = undoOperations;
        result.Success = result.Errors.Count == 0;

        // Store undo state
        if (undoOperations.Count > 0)
        {
            _undoStates[folder.Id] = new OrganizationUndoState
            {
                FolderId = folder.Id,
                Timestamp = DateTime.Now,
                Operations = undoOperations
            };
        }

        return result;
    }

    private async Task<List<MoveOperation>> ExecuteRuleActionsAsync(
        FileOrganizeResult result,
        string basePath,
        AppSettings settings)
    {
        var operations = new List<MoveOperation>();
        var currentFilePath = result.SourcePath;
        var currentFileName = Path.GetFileName(currentFilePath);
        var currentDirectory = Path.GetDirectoryName(currentFilePath)!;

        foreach (var action in result.Actions)
        {
            switch (action.Type)
            {
                case ActionType.MoveToFolder:
                    {
                        var destFolder = action.Value;
                        if (!Path.IsPathRooted(destFolder))
                            destFolder = Path.Combine(basePath, destFolder);

                        var targetPath = Path.Combine(destFolder, currentFileName);
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        await Task.Run(() => File.Move(currentFilePath, destPath));

                        operations.Add(new MoveOperation
                        {
                            OriginalPath = currentFilePath,
                            NewPath = destPath,
                            ActionType = "move"
                        });

                        currentFilePath = destPath;
                        currentFileName = Path.GetFileName(destPath);
                        currentDirectory = destFolder;
                    }
                    break;

                case ActionType.CopyToFolder:
                    {
                        var destFolder = action.Value;
                        if (!Path.IsPathRooted(destFolder))
                            destFolder = Path.Combine(basePath, destFolder);

                        var targetPath = Path.Combine(destFolder, currentFileName);
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        await Task.Run(() => File.Copy(currentFilePath, destPath));

                        operations.Add(new MoveOperation
                        {
                            OriginalPath = currentFilePath,
                            NewPath = destPath,
                            ActionType = "copy"
                        });
                    }
                    break;

                case ActionType.MoveToCategory:
                    {
                        var categoryId = action.Value;
                        var categories = _categoryService.GetCategories();
                        var category = categories.FirstOrDefault(c => c.Id == categoryId);

                        if (category != null)
                        {
                            var destFolder = Path.IsPathRooted(category.Destination)
                                ? category.Destination
                                : Path.Combine(basePath, category.Destination);

                            var targetPath = Path.Combine(destFolder, currentFileName);
                            if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                                break;

                            Directory.CreateDirectory(destFolder);
                            var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                            await Task.Run(() => File.Move(currentFilePath, destPath));

                            operations.Add(new MoveOperation
                            {
                                OriginalPath = currentFilePath,
                                NewPath = destPath,
                                ActionType = "move"
                            });

                            currentFilePath = destPath;
                            currentFileName = Path.GetFileName(destPath);
                            currentDirectory = destFolder;
                        }
                    }
                    break;

                case ActionType.SortIntoSubfolder:
                    {
                        var fileInfo = new FileInfo(result.SourcePath);
                        var subfolderName = RuleService.ExpandPattern(action.Value, fileInfo);
                        subfolderName = subfolderName.Replace('/', Path.DirectorySeparatorChar);
                        var destFolder = Path.Combine(basePath, subfolderName);

                        var targetPath = Path.Combine(destFolder, currentFileName);
                        if (currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase))
                            break;

                        Directory.CreateDirectory(destFolder);
                        var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                        await Task.Run(() => File.Move(currentFilePath, destPath));

                        operations.Add(new MoveOperation
                        {
                            OriginalPath = currentFilePath,
                            NewPath = destPath,
                            ActionType = "move"
                        });

                        currentFilePath = destPath;
                        currentFileName = Path.GetFileName(destPath);
                        currentDirectory = destFolder;
                    }
                    break;

                case ActionType.Rename:
                    {
                        var fileInfo = new FileInfo(result.SourcePath);
                        var newName = RuleService.ExpandPattern(action.Value, fileInfo);
                        var targetPath = Path.Combine(currentDirectory, newName);

                        if (currentFilePath.Equals(targetPath, StringComparison.Ordinal))
                            break;

                        var isCaseOnlyRename = currentFilePath.Equals(targetPath, StringComparison.OrdinalIgnoreCase);

                        if (isCaseOnlyRename)
                        {
                            var tempPath = currentFilePath + ".tmp_rename";
                            await Task.Run(() =>
                            {
                                File.Move(currentFilePath, tempPath);
                                File.Move(tempPath, targetPath);
                            });
                        }
                        else
                        {
                            var destPath = GetUniqueFilePath(targetPath, currentFilePath);
                            await Task.Run(() => File.Move(currentFilePath, destPath));
                            targetPath = destPath;
                        }

                        operations.Add(new MoveOperation
                        {
                            OriginalPath = currentFilePath,
                            NewPath = targetPath,
                            ActionType = "rename"
                        });

                        currentFilePath = targetPath;
                        currentFileName = Path.GetFileName(targetPath);
                    }
                    break;

                case ActionType.Delete:
                    {
                        if (settings.MoveToTrashInsteadOfDelete)
                        {
                            await Task.Run(() => MoveToRecycleBin(currentFilePath));
                        }
                        else
                        {
                            await Task.Run(() => File.Delete(currentFilePath));
                        }

                        operations.Add(new MoveOperation
                        {
                            OriginalPath = currentFilePath,
                            NewPath = "[deleted]",
                            ActionType = "delete"
                        });
                        return operations; // File no longer exists, stop processing
                    }

                case ActionType.Ignore:
                case ActionType.Continue:
                    break;
            }
        }

        return operations;
    }

    private async Task<MoveOperation?> ExecuteCategoryMoveAsync(
        FileOrganizeResult result,
        string basePath,
        AppSettings settings)
    {
        if (result.DestinationPath == null)
            return null;

        var destDir = Path.GetDirectoryName(result.DestinationPath)!;
        Directory.CreateDirectory(destDir);

        var finalPath = GetUniqueFilePath(result.DestinationPath, result.SourcePath);
        await Task.Run(() => File.Move(result.SourcePath, finalPath));

        return new MoveOperation
        {
            OriginalPath = result.SourcePath,
            NewPath = finalPath,
            ActionType = "move"
        };
    }

    /// <summary>
    /// Undoes the last organization operation for a folder.
    /// </summary>
    /// <param name="folderId">The folder ID.</param>
    /// <param name="progress">Optional progress reporter.</param>
    /// <returns>Result of the undo operation.</returns>
    public async Task<UndoResult> UndoLastOrganizationAsync(
        string folderId,
        IProgress<OrganizationProgress>? progress = null)
    {
        var result = new UndoResult();

        if (!_undoStates.TryRemove(folderId, out var undoState))
        {
            result.Error = "No undo history available for this folder.";
            return result;
        }

        var totalOps = undoState.Operations.Count;
        var processedCount = 0;

        // Process in reverse order
        foreach (var op in undoState.Operations.AsEnumerable().Reverse())
        {
            processedCount++;
            progress?.Report(new OrganizationProgress
            {
                CurrentFile = processedCount,
                TotalFiles = totalOps,
                CurrentFileName = Path.GetFileName(op.OriginalPath),
                CurrentAction = "Undoing"
            });

            try
            {
                switch (op.ActionType)
                {
                    case "move":
                    case "rename":
                        if (File.Exists(op.NewPath))
                        {
                            var originalDir = Path.GetDirectoryName(op.OriginalPath);
                            if (!string.IsNullOrEmpty(originalDir))
                            {
                                Directory.CreateDirectory(originalDir);
                            }
                            await Task.Run(() => File.Move(op.NewPath, op.OriginalPath));
                            result.FilesRestored++;
                        }
                        break;

                    case "copy":
                        if (File.Exists(op.NewPath))
                        {
                            await Task.Run(() => File.Delete(op.NewPath));
                            result.CopiesDeleted++;
                        }
                        break;

                    case "delete":
                        // Cannot undo deletions automatically
                        result.Warnings.Add($"Cannot restore deleted file: {op.OriginalPath}");
                        break;
                }
            }
            catch (Exception ex)
            {
                result.Errors.Add($"Failed to undo {op.OriginalPath}: {ex.Message}");
            }
        }

        result.Success = result.Errors.Count == 0;
        return result;
    }

    /// <summary>
    /// Checks if undo is available for a folder.
    /// </summary>
    public bool HasUndoState(string folderId)
    {
        return _undoStates.ContainsKey(folderId);
    }

    /// <summary>
    /// Gets the undo state for a folder.
    /// </summary>
    public OrganizationUndoState? GetUndoState(string folderId)
    {
        _undoStates.TryGetValue(folderId, out var state);
        return state;
    }

    /// <summary>
    /// Clears the undo state for a folder.
    /// </summary>
    public void ClearUndoState(string folderId)
    {
        _undoStates.TryRemove(folderId, out _);
    }

    private static bool IsFileLocked(string filePath)
    {
        try
        {
            using var stream = File.Open(filePath, FileMode.Open, FileAccess.ReadWrite, FileShare.None);
            return false;
        }
        catch (IOException)
        {
            return true;
        }
    }

    private static string GetUniqueFilePath(string path, string? sourcePathToExclude = null)
    {
        if (!File.Exists(path)) return path;
        if (sourcePathToExclude != null && path.Equals(sourcePathToExclude, StringComparison.OrdinalIgnoreCase))
            return path;

        var directory = Path.GetDirectoryName(path) ?? "";
        var name = Path.GetFileNameWithoutExtension(path);
        var extension = Path.GetExtension(path);

        var counter = 1;
        string newPath;

        do
        {
            newPath = Path.Combine(directory, $"{name} ({counter}){extension}");
            counter++;
        }
        while (File.Exists(newPath) && (sourcePathToExclude == null || !newPath.Equals(sourcePathToExclude, StringComparison.OrdinalIgnoreCase)));

        return newPath;
    }

    private static void MoveToRecycleBin(string filePath)
    {
        Microsoft.VisualBasic.FileIO.FileSystem.DeleteFile(
            filePath,
            Microsoft.VisualBasic.FileIO.UIOption.OnlyErrorDialogs,
            Microsoft.VisualBasic.FileIO.RecycleOption.SendToRecycleBin);
    }
}

/// <summary>
/// Detailed result of an organization operation.
/// </summary>
public class DetailedOrganizationResult
{
    public string FolderId { get; set; } = "";
    public string FolderPath { get; set; } = "";
    public bool Success { get; set; }
    public bool WasCancelled { get; set; }
    public int FilesProcessed { get; set; }
    public int FilesMoved { get; set; }
    public int FilesCopied { get; set; }
    public int FilesDeleted { get; set; }
    public int FilesSkipped { get; set; }
    public List<(string FilePath, string Error)> Errors { get; set; } = new();
    public TimeSpan Duration { get; set; }
    public DateTime StartTime { get; set; }
    public DateTime EndTime { get; set; }
    public List<MoveOperation> MoveOperations { get; set; } = new();
}

/// <summary>
/// State for undoing an organization operation.
/// </summary>
public class OrganizationUndoState
{
    public string FolderId { get; set; } = "";
    public DateTime Timestamp { get; set; }
    public List<MoveOperation> Operations { get; set; } = new();
}

/// <summary>
/// Represents a file move operation for undo tracking.
/// </summary>
public class MoveOperation
{
    public string OriginalPath { get; set; } = "";
    public string NewPath { get; set; } = "";
    public string ActionType { get; set; } = ""; // "move", "copy", "delete", "rename"
}

/// <summary>
/// Result of an undo operation.
/// </summary>
public class UndoResult
{
    public bool Success { get; set; }
    public int FilesRestored { get; set; }
    public int CopiesDeleted { get; set; }
    public string? Error { get; set; }
    public List<string> Errors { get; set; } = new();
    public List<string> Warnings { get; set; } = new();
}
