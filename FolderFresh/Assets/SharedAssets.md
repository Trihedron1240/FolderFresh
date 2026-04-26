# Windows Assets

FolderFresh is a Windows-first WinUI 3 app. Keep shared app imagery in this
directory and mark assets as `Content` when they need to be copied with the
desktop build.

### Examples

```text
\Assets\Images\logo.scale-100.png
\Assets\Images\logo.scale-200.png
\Assets\Images\logo.scale-400.png

\Assets\Images\scale-100\logo.png
\Assets\Images\scale-200\logo.png
\Assets\Images\scale-400\logo.png
```

### WinUI scale suffixes

| Scale | WinUI suffix |
|-------|:------------:|
| `100` | scale-100    |
| `125` | scale-125    |
| `150` | scale-150    |
| `200` | scale-200    |
| `300` | scale-300    |
| `400` | scale-400    |
