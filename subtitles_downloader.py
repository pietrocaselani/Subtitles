#!/usr/bin/python3 -u

import os
import argparse
from pathlib import Path
from babelfish import Language
from subliminal import download_best_subtitles, region, save_subtitles, scan_videos
from score_functions import dexter_2006_compute_score

script_dir = os.path.dirname(os.path.abspath(__file__))
cache_file = os.path.join(script_dir, 'cachefile.dbm')

# Configure the cache
region.configure('dogpile.cache.dbm', arguments={'filename': cache_file})

def download_subtitles_for_videos(video_folder: Path, language_code: str, should_report: bool):
    # Scan for videos and their existing subtitles
    print(f"Scanning for video files in {video_folder}")
    videos = [video for video in scan_videos(video_folder) if "sample" not in video.name.lower()]

    if not videos:
        print("No video files found in the specified folder.")
        return

    print(f"Found {len(videos)} video file(s). Searching for {language_code} subtitles...")

    # Parse language code for babelfish
    if '-' in language_code:
        lang, country = language_code.split('-', 1)
        language = Language(lang, country)
    else:
        language = Language(language_code)

    # Download the best subtitles
    subtitles = download_best_subtitles(videos, {language})

    saved_subtitles = []

    # Save subtitles next to the video files
    for video in videos:
        video_sub = subtitles[video]
        if video_sub:
            saved_subtitles.extend(save_subtitles(video, video_sub, encoding='utf-8'))
            print(f"Saved subtitles for: {video.name}")

        else:
            print(f"No subtitles found for: {video.name}")

    if saved_subtitles and should_report:
        report_path = os.path.join(video_folder, "subtitles_report.txt")

        try:
            with open(report_path, 'w', encoding='utf-8') as report_file:
                report_file.write("Subtitle Download Report\n")
                report_file.write("=" * 40 + "\n\n")

                for i, subtitle in enumerate(saved_subtitles, 1):
                    report_file.write(f"Subtitle {i}:\n")
                    report_file.write(f"  Provider: {getattr(subtitle, 'provider_name', 'N/A')}\n")
                    report_file.write(f"  Info: {getattr(subtitle, 'info', 'N/A')}\n")
                    report_file.write(f"  Id: {getattr(subtitle, 'id', 'N/A')}\n")
                    report_file.write(f"  Filename: {getattr(subtitle, 'filename', 'N/A')}\n")
                    report_file.write(f"  Encoding: {getattr(subtitle, 'encoding', 'N/A')}\n")
                    report_file.write(f"  Language: {getattr(subtitle, 'language', 'N/A')}\n")
                    report_file.write(f"  Movie name: {getattr(subtitle, 'movie_name', 'N/A')}\n")
                    report_file.write(f"  Movie release: {getattr(subtitle, 'movie_release_name', 'N/A')}\n")
                    report_file.write("\n")

            print(f"Report saved to: {report_path}")
        except Exception as e:
            print(f"Error writing report: {e}")

    print("Subtitle download complete.")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Download subtitles for video files in a directory.")
    parser.add_argument("directory", help="Path to the directory containing video files.")
    parser.add_argument("-l", "--language-code", default="por-BR", help="Subtitle language code (default: por-BR)")
    parser.add_argument("-r", "--report-file", default=False, help="True if should create a report file (default: False)")
    args = parser.parse_args()

    video_folder = Path(os.path.abspath(args.directory))
    language_code = args.language_code
    should_report = args.report_file

    # Validate the directory
    if not video_folder.is_dir():
        print(f"Error: The directory '{video_folder}' does not exist.")
        return

    download_subtitles_for_videos(video_folder, language_code, should_report)

if __name__ == "__main__":
    main()
