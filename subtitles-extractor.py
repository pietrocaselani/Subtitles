import sys
import subprocess
import json
import os
import glob
import argparse
from subliminal import scan_videos
from subliminal.subtitle import FORMAT_TO_EXTENSION
from tabulate import tabulate
import concurrent.futures
import multiprocessing
from convert_sup_to_srt import convert_sup_to_srt

FORMAT_TO_EXTENSION = {
    'srt': '.srt',
    'ass': '.ass',
    'ssa': '.ssa',
    'microdvd': '.sub',
    'mpl2': '.mpl',
    'tmp': '.txt',
    'vtt': '.vtt',
    'hdmv_pgs_subtitle': '.sup',  # Blu-ray PGS subtitles
    'dvd_subtitle': '.sub',       # VOBSUB (DVD subtitles)
}

def list_subtitle_tracks(video_file):
    if not os.path.isfile(video_file):
        print(f"File not found: {video_file}")
        return []
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "s",
        "-show_entries", "stream=index,codec_name,codec_type:stream_tags=language,title",
        "-of", "json",
        video_file
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        streams = info.get("streams", [])
        tracks = []
        for index_position, stream in enumerate(streams):
            idx = stream.get("index")
            tags = stream.get("tags", {})
            lang = tags.get("language", "unknown")
            title = tags.get("title", "")
            codec_type = stream.get("codec_type", "unknown")
            codec_name = stream.get("codec_name", "unknown")
            tracks.append({
                "index": idx,
                "index_position": index_position,
                "language": lang,
                "title": title,
                "codec_type": codec_type,
                "codec_name": codec_name
            })
        return tracks
    except subprocess.CalledProcessError as e:
        print(f"ffprobe error: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []

def extract_subtitle(video_file, stream_index_position, output_file):
    cmd = [
        "ffmpeg",
        "-i", video_file,
        "-map", f"0:s:{stream_index_position}",
        "-c", "copy",
        "-an", "-vn",
        output_file,
        "-y"
    ]
    print(f"Running: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)

def convert_subtitle_to_srt(input_file, output_file):
    ext = os.path.splitext(input_file)[1].lower()
    if ext == ".sup":
        print(f"SUP detected, using OCR pipeline for {input_file}")
        convert_sup_to_srt(input_file, output_file)
        return
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        output_file
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, capture_output=True, text=True)

def subtitle_track_selection(tracks, language):
    matching_tracks = [track for track in tracks if track["language"] == language]
    if not matching_tracks:
        print(f"No subtitle track found for language: {language}")
        return None

    return matching_tracks[0]

def process_video_file(video_filepath, language):
    print(f"Processing video: {video_filepath}")
    result = {
        "video_filepath": video_filepath,
        "track": None,
        "status": None,
        "message": None,
        "subtitle_file_original": None,
        "subtitle_file_srt": None
    }

    tracks = list_subtitle_tracks(video_filepath)
    if not tracks:
        print("No subtitle tracks found.")
        result["status"] = "no_tracks"
        result["message"] = "No subtitle tracks found"
        return result

    print("Subtitle Tracks:")
    print(tabulate(tracks, headers="keys"))

    track = subtitle_track_selection(tracks, language)
    if not track:
        print(f"No suitable subtitle track found for language '{language}'.")
        result["status"] = "no_lang_track"
        result["message"] = f"No track for language {language}"
        return result

    result["track"] = track

    print(f"Selected track: Index: {track['index']}, Title: '{track['title']}', Codec: {track['codec_name']}")

    extension = FORMAT_TO_EXTENSION.get(track["codec_name"].lower(), ".srt")

    if not extension:
        result["status"] = "unsupported_subtitle_format"
        result["message"] = f"Unsupported subtitle format: {track['codec_name']}"
        return result

    filename_wo_ext = os.path.splitext(os.path.basename(video_filepath))[0]
    subtitle_file_original = os.path.join(
        os.path.dirname(video_filepath),
        f"{filename_wo_ext}.{track['language']}{extension}"
    )

    subtitle_file_srt = os.path.join(
        os.path.dirname(video_filepath),
        f"{filename_wo_ext}.{track['language']}.srt"
    )
    result["subtitle_file_srt"] = subtitle_file_srt

    result["subtitle_file_original"] = subtitle_file_original

    if os.path.exists(subtitle_file_srt):
        print(f"SRT subtitle file already exists: {subtitle_file_srt}")
        result["status"] = "srt_exists"
        result["message"] = f"SRT exists: {subtitle_file_srt}"
        return result

    if os.path.exists(subtitle_file_original):
        print(f"Subtitle {track['codec_name']} file already exists: {subtitle_file_original}")
        result["status"] = "already_extracted"
        result["message"] = f"Subtitle file exists: {subtitle_file_original}"
    else:
        print(f"Extracting subtitle track {track['index']} to {subtitle_file_original}")
        try:
            extract_subtitle(video_filepath, track["index_position"], subtitle_file_original)
            result["status"] = "extracted"
            result["message"] = f"Extracted to {subtitle_file_original}"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Extraction failed: {e}"
            return result

    # Convert the extracted subtitle to SRT if it's not already SRT
    if track["codec_name"].lower() != "subrip":
        print(f"Converting {subtitle_file_original} to SRT: {subtitle_file_srt}")
        try:
            convert_subtitle_to_srt(subtitle_file_original, subtitle_file_srt)
            print(f"Converted to SRT: {subtitle_file_srt}")
            result["status"] = "converted"
            result["message"] = f"Converted to SRT: {subtitle_file_srt}"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Conversion failed: {e}"
    else:
        print(f"Subtitle is already in SRT format: {subtitle_file_original}")
        result["status"] = "already_srt"
        result["message"] = f"Already SRT: {subtitle_file_original}"
    return result

def main():
    parser = argparse.ArgumentParser(description="Extract and convert subtitles from video files.")
    parser.add_argument("directory", help="Path to the directory containing video files.")
    parser.add_argument("-l", "--language", default="eng", help="Subtitle language code (default: eng)")
    args = parser.parse_args()

    video_folder = os.path.abspath(args.directory)
    language = args.language
    max_workers = 1

    print(f"Video folder: {video_folder}")
    print(f"Language: {language}")
    print(f"Max workers: {max_workers}")

    if not os.path.isdir(video_folder):
        print(f"Error: The directory '{video_folder}' does not exist.")
        return

    print(f"Scanning for video files in {video_folder}")
    videos_filepaths = [video.name for video in scan_videos(video_folder) if "sample" not in video.name]
    if not videos_filepaths:
        print("No video files found in the specified folder.")
        return

    print(f"Found {len(videos_filepaths)} video file(s).")
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_video = {executor.submit(process_video_file, video_filepath, language): video_filepath for video_filepath in videos_filepaths}
        for future in concurrent.futures.as_completed(future_to_video):
            result = future.result()
            results.append(result)

    print("\nSummary:")
    summary_rows = []
    for r in results:
        summary_rows.append([
            os.path.basename(r["video_filepath"]),
            r["status"],
            r.get("track", {}).get("index") if r.get("track") else None,
            r.get("track", {}).get("language") if r.get("track") else None,
            r.get("track", {}).get("codec_name") if r.get("track") else None,
            r["message"]
        ])
    print(tabulate(summary_rows, headers=["Video", "Status", "TrackIdx", "Lang", "Codec", "Message"]))

if __name__ == "__main__":
    main()