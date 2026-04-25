# All-Subtitles Toolkit

A collection of Python scripts for batch subtitle extraction, conversion, downloading, and synchronization. This toolkit is designed to help you efficiently manage subtitles for your video library, including advanced features like OCR for image-based subtitles, language code support, and robust file matching.

## Features

- **Batch subtitle extraction and conversion** (including OCR for .sup/PGS files)
- **Subtitle downloading** with language code support
- **Subtitle synchronization** using audio or reference subtitles

---

## Requirements

- Python 3.7+
- [ffmpeg](https://ffmpeg.org/) (for subtitle extraction)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (for OCR on .sup/PGS files)
- [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit) (optional, for .sup to .srt conversion)
- [alass-cli](https://github.com/kaegi/alass) (for subtitle synchronization)
- [subliminal](https://github.com/Diaoul/subliminal) (for subtitle downloading)
- Python packages: see `requirements.txt`

---

## Installation

1. Clone the repository:
   ```sh
   git clone <this-repo-url>
   cd all-subtitles
   ```
2. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Install required external tools (ffmpeg, Tesseract, Subtitle Edit, alass-cli) and ensure they are in your system PATH.

---

## Script Summaries

### 1. `subtitles_extractor.py`

**Purpose:**
Batch-extracts and converts subtitles from video files. Supports OCR for .sup/PGS files using Tesseract or Subtitle Edit. Handles multiple files in parallel and supports language code detection in filenames.

**Usage:**

```sh
python subtitles_extractor.py <directory> [--language-code <code>]
```

- `<directory>`: Directory containing video files.
- `--language-code`: Language code for output subtitles (e.g., `eng`, `pt-BR`).

### 2. `convert_sup_to_srt.py`

**Purpose:**
Converts .sup (PGS) subtitle files to .srt using OCR. Supports both Tesseract and Subtitle Edit as backends. Can be used standalone or as a module.

**Usage:**

```sh
python convert_sup_to_srt.py --input <file.sup> --output <file.srt> [--method tesseract|subtitleedit] [--lang <code>]
```

- `--input`: Input .sup file.
- `--output`: Output .srt file.
- `--method`: OCR method (`tesseract` or `subtitleedit`).
- `--lang`: Language code for OCR (e.g., `eng`, `por`).

### 3. `subtitles_downloader.py`

**Purpose:**
Downloads subtitles for video files in a directory using the `subliminal` library. Supports specifying the desired language code.

**Usage:**

```sh
python subtitles_downloader.py --input-dir <directory> [--language-code <code>]
```

- `--input-dir`: Directory containing video files.
- `--language-code`: Language code for subtitles (default: `pt-BR`).

### 4. `subtitles_sync.py`

**Purpose:**
Synchronizes subtitle files with their corresponding videos or with a reference subtitle using `alass-cli`. Handles language codes in filenames and robustly matches files. Moves old subtitles to an `old-subtitles` folder for backup.

**Usage:**
Run interactively:

```sh
python subtitles_sync.py
```

You will be prompted for:

- Directory containing video and subtitle files
- Audio index (optional)
- Reference language code (e.g., `eng`)
- Target language code (e.g., `pt-BR`)

### 5. `subtitles_uploader.mjs`

**Purpose:**
Uploads subtitle files to OpenSubtitles platform. Matches video files with their corresponding .srt subtitles, fetches movie/episode details from TMDB, and performs batch uploads. Tracks uploaded subtitles and failed attempts in result files.

**Requirements:**

- Node.js 16+
- npm packages: `opensubtitles-api`, `guessit-js`, `mediainfo-wrapper`, `node-fetch`

**Installation:**

```sh
npm install
```

**Usage:**

```sh
node subtitles_uploader.mjs <directory> <config.json>
```

- `<directory>`: Directory containing video and subtitle files to upload.
- `<config.json>`: Path to configuration file with credentials and API keys.

**Configuration File (`config.json`):**

```json
{
  "opensubtitles": {
    "username": "user",
    "password": "pass"
  },
  "tmdb_api": "my-api-key",
  "upload_results_path": "upload_results.jsonl",
  "upload_fails_path": "upload_results_fails.jsonl"
}
```

**Configuration Fields:**

- `opensubtitles.username`: Your OpenSubtitles username
- `opensubtitles.password`: Your OpenSubtitles password
- `tmdb_api`: Your TMDB (The Movie Database) API key
- `upload_results_path`: Path to save successful upload logs (JSONL format)
- `upload_fails_path`: Path to save failed upload logs (JSONL format)

**Features:**

- Automatically matches video files with .srt subtitle files
- Prefers Portuguese (pt-BR/pob) subtitles if multiple options exist
- Fetches IMDB and media details from TMDB to enhance uploads
- Skips already-uploaded subtitles (caches results)
- Logs all upload attempts and failures
- Supports multiple video formats: .mkv, .mp4, .avi, .mov

---

## Environment Setup

- Ensure all required tools are installed and available in your system PATH.
- For Tesseract OCR, install the appropriate language data files (e.g., `eng.traineddata`, `por.traineddata`).
- On Windows, you may need to set environment variables for Tesseract and Subtitle Edit if not in PATH.

---

## Tips

- For best results, keep video and subtitle files in the same directory, using language codes in filenames (e.g., `movie.eng.srt`, `movie.pt-BR.srt`).
- Use the `old-subtitles` folder as a backup when synchronizing subtitles.
- Check script output for error messages and status updates.

---

## Acknowledgments

- [ffmpeg](https://ffmpeg.org/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit)
- [alass-cli](https://github.com/kaegi/alass)
- [subliminal](https://github.com/Diaoul/subliminal)
