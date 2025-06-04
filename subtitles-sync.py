#!/usr/bin/python3 -u

import os
import subprocess
import chardet
import shutil

from subliminal import scan_videos

# https://github.com/smacke/ffsubsync
# https://github.com/kaegi/alass

# Define video and subtitle extensions
video_extensions = ('.mp4', '.mkv', '.avi')
subtitle_extensions = ('.srt', '.sub', '.txt')

def ensure_utf8_encoding(file_path):
    # Detect the encoding of the subtitle file
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    # Read the file with the detected encoding
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()

    # Write the content back as UTF-8
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def synchronize_subtitles_by_video(video_file, subtitle_file, old_subtitles_dir, audio_index=None):
    input_video_path = os.path.join(directory, video_file)
    input_subtitle_path = os.path.join(directory, subtitle_file)
    subtitle_name, subtitle_ext = os.path.splitext(subtitle_file)
    temp_subtitle_path = os.path.join(directory, f"{subtitle_name}.temp{subtitle_ext}")

    print(f"Synchronizing: {video_file} with {subtitle_file}")

    # Ensure the subtitle file is encoded as UTF-8
    try:
        ensure_utf8_encoding(input_subtitle_path)
    except Exception as e:
        print(f"Error encoding subtitle file {subtitle_file} as UTF-8: {e}")
        return

    # Call the alass-cli command
    try:
        command = ["alass-cli"]
        if audio_index is not None:
            command.extend(["--index", str(audio_index)])
        command.extend([input_video_path, input_subtitle_path, temp_subtitle_path])

        subprocess.run(command, check=True)
        print(f"Synced subtitle saved to: {temp_subtitle_path}")

        # Move the original subtitle file to "old-subtitles" folder
        old_subtitle_path = os.path.join(old_subtitles_dir, subtitle_file)
        shutil.move(input_subtitle_path, old_subtitle_path)

        # Move the temporary subtitle file to the original subtitle path
        shutil.move(temp_subtitle_path, input_subtitle_path)
    except subprocess.CalledProcessError as e:
        print(f"Error while syncing {video_file} and {subtitle_file}: {e}")
        if os.path.exists(temp_subtitle_path):
            os.remove(temp_subtitle_path)

def synchronize_subtitles_by_reference(subtitle_file_to_sync, reference_subtitle_file, old_subtitles_dir):
    # Prepare paths
    input_subtitle_path = os.path.join(directory, subtitle_file_to_sync)
    reference_subtitle_path = os.path.join(directory, reference_subtitle_file)
    subtitle_name, subtitle_ext = os.path.splitext(subtitle_file_to_sync)
    temp_subtitle_path = os.path.join(directory, f"{subtitle_name}.temp{subtitle_ext}")

    print(f"Synchronizing: {subtitle_file_to_sync} with {reference_subtitle_file}")

    # Ensure the subtitle file is encoded as UTF-8
    try:
        ensure_utf8_encoding(input_subtitle_path)
    except Exception as e:
        print(f"Error encoding subtitle file {subtitle_file_to_sync} as UTF-8: {e}")
        return



    # Call the alass-cli command: alass-cli reference_subtitle.ssa incorrect_subtitle.srt output.srt
    try:
        command = ["alass-cli", reference_subtitle_path, input_subtitle_path, temp_subtitle_path]
        subprocess.run(command, check=True)
        print(f"Synced subtitle saved to: {temp_subtitle_path}")

        # Move the original subtitle file to "old-subtitles" folder
        old_subtitle_path = os.path.join(old_subtitles_dir, subtitle_file_to_sync)
        shutil.move(input_subtitle_path, old_subtitle_path)

        # Move the temporary subtitle file to the original subtitle path
        shutil.move(temp_subtitle_path, input_subtitle_path)
    except subprocess.CalledProcessError as e:
        print(f"Error while syncing {subtitle_file_to_sync} and {reference_subtitle_file}: {e}")
        if os.path.exists(temp_subtitle_path):
            os.remove(temp_subtitle_path)


def process_files(directory, target_language, reference_language, audio_index=None):
    """
    Synchronize subtitles for all video files in the given directory.

    Parameters:
    directory (str): The path to the directory containing video and subtitle files.
    audio_index (int, optional): The index of the audio track to use for synchronization.

    """
    # List all files in the directory
    files = os.listdir(directory)

    videos = [video.name for video in scan_videos(directory) if "sample" not in video.name.lower()]

    # Separate video and subtitle files
    # videos = [f for f in files if f.lower().endswith(video_extensions)]
    subtitle_files = [f for f in files if f.lower().endswith(subtitle_extensions)]

    print(f"Number of video files: {len(videos)}")
    print(f"Number of subtitle files: {len(subtitle_files)}")

    # Create "old-subtitles" folder if it doesn't exist
    old_subtitles_dir = os.path.join(directory, "old-subtitles")
    if not os.path.exists(old_subtitles_dir):
        os.makedirs(old_subtitles_dir)

    # Match video files with subtitles by their filenames (ignoring extensions and language codes)
    for video_file in videos:
        video_basename, _ = os.path.splitext(os.path.basename(video_file))
        # Match subtitles that start with the video_basename and have a language code (or not) before the extension
        matching_subtitles = [
            s for s in subtitle_files
            if os.path.splitext(s)[0] == video_basename or os.path.splitext(s)[0].startswith(video_basename + ".")
        ]

        # Try to find a subtitle that matches the target language
        subtitle_file_to_sync = None
        for s in matching_subtitles:
            parts = os.path.splitext(s)[0].split('.')
            if len(parts) > 1 and parts[-1].lower() == target_language.lower():
                subtitle_file_to_sync = s
                break

        reference_subtitle_file = None
        for s in matching_subtitles:
            parts = os.path.splitext(s)[0].split('.')
            if len(parts) > 1 and parts[-1].lower() == reference_language.lower():
                reference_subtitle_file = s
                break

        if reference_subtitle_file and subtitle_file_to_sync:
            print(f"Found reference subtitle: {reference_subtitle_file} for {video_file}")
            synchronize_subtitles_by_reference(subtitle_file_to_sync, reference_subtitle_file, old_subtitles_dir)
        else:
            if not subtitle_file_to_sync and matching_subtitles:
                subtitle_file_to_sync = matching_subtitles[0]

            if matching_subtitles:
                synchronize_subtitles_by_video(video_file, subtitle_file_to_sync, old_subtitles_dir, audio_index)
            else:
                print(f"No matching subtitle found for: {video_file}")

if __name__ == "__main__":
    # Get directory input from the user
    directory = input("Enter the directory containing video and subtitle files: ").strip()
    audio_index = input("Enter the audio index (or press Enter to skip): ").strip()
    reference_language = input("Enter the reference language: ").strip()
    target_language = input("Enter the language to sync: ").strip()
    audio_index = int(audio_index) if audio_index else None

    if not target_language:
        print("No target language provided. Exiting.")
        exit(1)

    # Check if the directory exists
    if os.path.isdir(directory):
        process_files(directory, target_language, reference_language, audio_index)
    else:
        print(f"The directory {directory} does not exist.")
