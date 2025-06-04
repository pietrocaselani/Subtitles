import os
import subprocess

def convert_sup_to_srt(input_file, output_file):
    """
    Convert a .sup (PGS) subtitle file to .srt using Subtitle Edit's CLI.

    Args:
        input_file (str): Path to the .sup file.
        output_file (str): Path to the output .srt file.
        tess_lang (str): Unused, kept for compatibility.
    """
    subtitle_edit_bin = r"C:\Users\pc199\Downloads\Apps\SubtitleEdit\SubtitleEdit.exe"
    cmd = [
        subtitle_edit_bin,
        "/convert",
        input_file,
        "SubRip",
        f"/outputfilename:{output_file}",
        "/encoding:utf-8"
    ]
    print(f"Running Subtitle Edit: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Subtitle Edit conversion complete: {output_file}")