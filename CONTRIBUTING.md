# Contributing To FolderFresh

Thanks for helping make FolderFresh a safer Windows file organiser.

## Project Focus

FolderFresh is a Windows file organizer, so changes should protect user trust and
file safety:

- Keep docs, screenshots, release notes, and the app's feature set aligned.
- Treat watcher, preview, undo, snapshot, and conflict-handling behavior carefully.
- Add tests for rule matching and file-operation behavior when those areas change.
- Keep starter profiles practical and easy to understand.
- Prefer Windows-native polish over broad platform expansion.

## Local Setup

```powershell
dotnet restore
dotnet build FolderFresh.sln -c Release
dotnet test FolderFresh.Tests\FolderFresh.Tests.csproj --collect:"XPlat Code Coverage"
dotnet run --project FolderFresh\FolderFresh.csproj
```

Use temporary folders when testing organization behavior. Do not test new rules on
important folders until Preview has shown the expected result.

## Pull Requests

- Keep changes focused and explain user-visible behavior.
- Add or update tests for rule matching, preview parity, watcher behavior, and file
  operation safety when those areas change.
- Update `README.md`, `ENGINE.md`, and `docs/index.html` when a feature changes.
- Keep public documentation limited to behavior that is implemented, tested, and
  visible in the app.

## Good First Issues

Useful starter work includes:

- Localisation review.
- Starter profile packs.
- Docs corrections.
- Tests for edge cases around locked files, duplicate names, and watched-folder
  loops.
- Packaging and release-validation improvements.
