#!/usr/bin/python3 -u

import os
import argparse

from babelfish import Language
from subliminal import download_best_subtitles, region, save_subtitles, scan_videos

script_dir = os.path.dirname(os.path.abspath(__file__))
cache_file = os.path.join(script_dir, 'cachefile.dbm')

# Configure the cache
region.configure('dogpile.cache.dbm', arguments={'filename': cache_file})

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Download subtitles for video files in a directory.")
    parser.add_argument("directory", help="Path to the directory containing video files.")
    parser.add_argument("-l", "--language-code", default="por-BR", help="Subtitle language code (default: por-BR)")
    args = parser.parse_args()

    video_folder = os.path.abspath(args.directory)
    language_code = args.language_code

    # Validate the directory
    if not os.path.isdir(video_folder):
        print(f"Error: The directory '{video_folder}' does not exist.")
        return

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

    # Save subtitles next to the video files
    for video in videos:
        video_sub = subtitles[video]
        if video_sub:
            save_subtitles(video, video_sub, encoding='utf-8')
            print(f"Saved subtitles for: {video.name}")
        else:
            print(f"No subtitles found for: {video.name}")

    print("Subtitle download complete.")

if __name__ == "__main__":
    main()
