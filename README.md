# 🐧 Linux Command Library

A personal collection of my most-used Linux terminal commands, scripts, and utilities.

This repository is designed as a quick-reference library. Commands are grouped by purpose and placed inside individual code blocks so they can be copied directly from GitHub and pasted into the Linux terminal.

> **Note:** Python commands assume the corresponding `.py` script is located in the current terminal directory.

---

# 🎬 Media & IMDb Tools

Python utilities used to scan, rename, restore, and verify media filenames using IMDb IDs.

## IMDb Media Scanner

Scans media files for IMDb-related information.

```bash
python3 imdb_media_scanner.py
```

---

## IMDb Filename Scanner

Scans filenames for IMDb information.

```bash
python3 imdb_filename_scanner.py
```

---

## IMDb ID Filename Scanner

Scans filenames specifically for IMDb IDs such as:

`tt0149460`

Useful for verifying which files already contain IMDb identifiers.

```bash
python3 imdbid_filename_scanner.py
```

---

## IMDb Filename Renamer

Renames media files using IMDb information.

Use this after the appropriate media or filename scan has been completed.

```bash
python3 imdb_filename_renamer.py
```

---

## IMDb Filename Restorer

Restores filenames after they have been modified by the IMDb filename renaming process.

Useful if a rename was incorrect or needs to be rolled back.

```bash
python3 imdb_filename_restorer.py
```

---

# ▶️ Video Downloads

Commands used with `yt-dlp` for downloading online video.

## Best Video + Audio to MKV

Downloads the best available video and audio streams and merges them into a single MKV file.

Replace the URL with the video you want to download.

### Generic Version

```bash
yt-dlp -f "bv*+ba/b" --merge-output-format mkv "VIDEO_URL"
```

---

# 🧠 Quiz & Study Tools

Python utilities used for studying and running CSV-based quizzes.

## CSV Quiz Application

Launches the CSV quiz application.

```bash
python3 csv_quiz_app.py
```

---

# 📄 PDF Tools

Commands used for splitting, converting, and processing PDF files.

## Split PDF into Individual Pages

Uses `pdftk` to burst PDF documents into individual PDF pages.

```bash
pdftk *.pdf burst
```

This operates on PDF files located in the current directory.

---

# 🖼️ PDF to PNG Conversion

Converts every PDF in the current directory into high-resolution PNG images.

The original filename is preserved.

```bash
for file in *.pdf; do convert -density 600 -background white -alpha remove -quality 100 "$file" "${file%.pdf}.png"; done
```

### What It Does

- Processes every `.pdf` in the current directory
- Renders at **600 DPI**
- Uses a **white background**
- Removes transparency
- Uses maximum image quality
- Keeps the original base filename

Example:

```text
training.pdf
```

becomes:

```text
training.png
```

> This command uses ImageMagick's `convert` command.

---

# 🔧 Useful Packages

Some commands in this repository require additional Linux packages.

## Install Python 3

```bash
sudo apt install python3
```

---

## Install yt-dlp

On systems where `pipx` is being used:

```bash
pipx install yt-dlp
```

Upgrade yt-dlp:

```bash
pipx upgrade yt-dlp
```

Check the installed version:

```bash
yt-dlp --version
```

---

## Install PDFtk

```bash
sudo apt install pdftk
```

---

## Install ImageMagick

```bash
sudo apt install imagemagick
```

Check the installation:

```bash
magick -version
```

or:

```bash
convert -version
```

---

# 📁 Running Python Scripts

Before running one of the Python utilities, move into the directory containing the script.

Example:

```bash
cd /path/to/scripts
```

Then run the script:

```bash
python3 script_name.py
```

To see the files in the current directory:

```bash
ls
```

To see your current directory:

```bash
pwd
```

---

# 📚 Categories

| Category | Purpose |
|---|---|
| 🎬 Media & IMDb | Media scanning, IMDb IDs, renaming, and filename restoration |
| ▶️ Video Downloads | yt-dlp download and conversion commands |
| 🧠 Study Tools | Quiz and learning applications |
| 📄 PDF Tools | PDF splitting and processing |
| 🖼️ Image Tools | PDF-to-image conversion |
| 🔧 Linux Setup | Installing utilities and dependencies |

---

# ⚠️ Usage Notes

Always verify your current directory before running commands that rename, convert, or modify multiple files.

```bash
pwd
```

Then inspect the directory:

```bash
ls
```

For scripts that alter filenames, running a scanner or preview step before the renaming operation is recommended.

---

# 🐧 Personal Linux Toolbox

This repository is intended to grow as I discover or create useful Linux commands.

Future sections may include:

- File management
- Bulk filename operations
- Jellyfin tools
- FFmpeg
- yt-dlp
- ImageMagick
- PDF processing
- Python utilities
- System maintenance
- Disk management
- Networking
- Git and GitHub
- Media organization
