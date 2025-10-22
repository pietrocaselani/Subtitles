#!/usr/bin/env python3
"""
Media Tracks Analyzer
Analyzes video files to display detailed information about audio, video, and subtitle tracks.
"""

import sys
import subprocess
import json
import argparse
from pathlib import Path

def get_ffprobe_info(video_path):
    """
    Use ffprobe to get detailed media information
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing ffprobe output: {e}")
        return None
    except FileNotFoundError:
        print("Error: ffprobe not found. Please install ffmpeg and ensure it's in your PATH.")
        return None


def format_duration(seconds):
    """
    Format duration from seconds to HH:MM:SS
    """
    if seconds is None:
        return "Unknown"

    try:
        seconds = float(seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "Unknown"


def format_bitrate(bitrate):
    """
    Format bitrate in a human-readable format
    """
    if bitrate is None:
        return "Unknown"

    try:
        bitrate = int(bitrate)
        if bitrate >= 1000000:
            return f"{bitrate / 1000000:.1f} Mbps"
        elif bitrate >= 1000:
            return f"{bitrate / 1000:.1f} kbps"
        else:
            return f"{bitrate} bps"
    except (ValueError, TypeError):
        return "Unknown"


def calculate_fps(fps_string):
    """
    Calculate FPS from fractional string format
    """
    if fps_string == 'Unknown' or '/' not in str(fps_string):
        return fps_string

    try:
        num, den = map(int, fps_string.split('/'))
        return f"{num/den:.2f}" if den != 0 else 'Unknown'
    except (ValueError, ZeroDivisionError):
        return 'Unknown'


def format_resolution(width, height):
    """
    Format resolution string
    """
    if width != 'Unknown' and height != 'Unknown':
        return f"{width}x{height}"
    return 'Unknown'


def analyze_video_streams(streams):
    """
    Analyze video streams and return formatted information
    """
    video_streams = []

    for i, stream in enumerate(streams):
        if stream.get('codec_type') == 'video':
            codec = stream.get('codec_name', 'Unknown')
            width = stream.get('width', 'Unknown')
            height = stream.get('height', 'Unknown')
            fps = calculate_fps(stream.get('r_frame_rate', 'Unknown'))
            bitrate = format_bitrate(stream.get('bit_rate'))
            duration = format_duration(stream.get('duration'))

            video_streams.append({
                'Index': stream.get('index', i),
                'Codec': codec.upper(),
                'Resolution': format_resolution(width, height),
                'FPS': fps,
                'Bitrate': bitrate,
                'Duration': duration
            })

    return video_streams


def analyze_audio_streams(streams):
    """
    Analyze audio streams and return formatted information
    """
    audio_streams = []

    for i, stream in enumerate(streams):
        if stream.get('codec_type') == 'audio':
            codec = stream.get('codec_name', 'Unknown')
            channels = stream.get('channels', 'Unknown')
            sample_rate = stream.get('sample_rate', 'Unknown')
            bitrate = format_bitrate(stream.get('bit_rate'))
            duration = format_duration(stream.get('duration'))

            # Get language
            tags = stream.get('tags', {})
            language = tags.get('language', tags.get('lang', 'Unknown'))

            # Get title/description
            title = tags.get('title', tags.get('handler_name', ''))

            audio_streams.append({
                'Index': stream.get('index', i),
                'Codec': codec.upper(),
                'Channels': channels,
                'Sample Rate': f"{sample_rate} Hz" if sample_rate != 'Unknown' else 'Unknown',
                'Bitrate': bitrate,
                'Language': language,
                'Title': title,
                'Duration': duration
            })

    return audio_streams


def analyze_subtitle_streams(streams):
    """
    Analyze subtitle streams and return formatted information
    """
    subtitle_streams = []

    for i, stream in enumerate(streams):
        if stream.get('codec_type') == 'subtitle':
            codec = stream.get('codec_name', 'Unknown')
            duration = format_duration(stream.get('duration'))

            # Get language
            tags = stream.get('tags', {})
            language = tags.get('language', tags.get('lang', 'Unknown'))

            # Get title/description
            title = tags.get('title', tags.get('handler_name', ''))

            # Check if forced or default
            disposition = stream.get('disposition', {})
            is_forced = disposition.get('forced', 0) == 1
            is_default = disposition.get('default', 0) == 1

            flags = []
            if is_default:
                flags.append('Default')
            if is_forced:
                flags.append('Forced')

            subtitle_streams.append({
                'Index': stream.get('index', i),
                'Codec': codec.upper(),
                'Language': language,
                'Title': title,
                'Flags': ', '.join(flags) if flags else '',
                'Duration': duration
            })

    return subtitle_streams


def print_table(title, data, headers):
    """
    Print a formatted table
    """
    if not data:
        print(f"\n{title}: None found")
        return

    print(f"\n{title}:")
    print("-" * len(title))

    # Create table data
    table_data = []
    for item in data:
        row = [str(item.get(header, '')) for header in headers]
        table_data.append(row)

    # Print table with proper formatting
    from tabulate import tabulate
    print(tabulate(table_data, headers=headers, tablefmt='grid'))

def get_media_info(video_path: Path):
    if not video_path.exists():
        print(f"Error: File '{video_path}' not found.")
        return False

    return get_ffprobe_info(video_path)

def print_media_file(video_path):
    """
    Main function to analyze a media file
    """

    video_path = Path(video_path)

    media_info = get_media_info(video_path)

    if not media_info:
        return False

    print(f"Analyzing: {video_path.name}")
    print(f"Full path: {video_path.absolute()}")
    print(f"File size: {video_path.stat().st_size / (1024*1024):.1f} MB")

    streams = media_info.get('streams', [])
    format_info = media_info.get('format', {})

    # Print general file information
    print("\nGeneral Information:")
    print("-" * 20)
    print(f"Format: {format_info.get('format_name', 'Unknown')}")
    print(f"Duration: {format_duration(format_info.get('duration'))}")
    print(f"Overall bitrate: {format_bitrate(format_info.get('bit_rate'))}")
    print(f"Total streams: {len(streams)}")

    # Analyze each type of stream
    video_streams = analyze_video_streams(streams)
    audio_streams = analyze_audio_streams(streams)
    subtitle_streams = analyze_subtitle_streams(streams)

    # Print results
    print_table("Video Streams", video_streams,
                ['Index', 'Codec', 'Resolution', 'FPS', 'Bitrate', 'Duration'])

    print_table("Audio Streams", audio_streams,
                ['Index', 'Codec', 'Channels', 'Sample Rate', 'Bitrate', 'Language', 'Title', 'Duration'])

    print_table("Subtitle Streams", subtitle_streams,
                ['Index', 'Codec', 'Language', 'Title', 'Flags', 'Duration'])

    return True


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(
        description='Analyze video files to display track information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python media-tracks.py video.mkv
  python media-tracks.py "C:\\Movies\\video.mp4"
  python media-tracks.py --file video.avi
        """
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='Video file to analyze'
    )

    parser.add_argument(
        '--file', '-f',
        dest='file_path',
        help='Video file to analyze (alternative to positional argument)'
    )

    args = parser.parse_args()

    # Determine which file to analyze
    video_file = args.file or args.file_path

    if not video_file:
        parser.print_help()
        print("\nError: Please specify a video file to analyze.")
        return 1

    try:
        success = print_media_file(video_file)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())