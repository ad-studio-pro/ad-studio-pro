"""
Video stitcher — extracts last frames and concatenates MP4s using ffmpeg.

Uses `imageio-ffmpeg` which bundles a static ffmpeg binary, so the user
doesn't have to install ffmpeg system-wide.
"""

import subprocess
from pathlib import Path


def get_ffmpeg() -> str:
    """Return path to ffmpeg binary (uses imageio-ffmpeg if available)."""
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except ImportError:
        # Last-resort: try a system ffmpeg (probably absent on Windows)
        import shutil
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg
        raise RuntimeError(
            "ffmpeg is not installed. Run 1_SETUP.bat again - it installs imageio-ffmpeg "
            "(a Python package that bundles ffmpeg.exe - no separate install needed)."
        )


def extract_last_frame(video_path: Path, output_path: Path) -> Path:
    """
    Extract the very last frame of a video as a JPG.

    -sseof -0.1 seeks 0.1s before end of file, then we grab one frame.
    """
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        get_ffmpeg(),
        "-y",                         # overwrite without asking
        "-sseof", "-0.5",             # 0.5s before end
        "-i", str(video_path),
        "-vframes", "1",              # one frame
        "-q:v", "2",                  # high quality
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg last-frame extract failed:\n{result.stderr[-500:]}")
    if not output_path.exists():
        raise RuntimeError(f"ffmpeg ran but {output_path} doesn't exist")
    return output_path


def concat_videos(video_paths: list, output_path: Path) -> Path:
    """
    Concatenate multiple MP4s into one.

    Uses ffmpeg's concat demuxer — fast (no re-encoding) when codecs match.
    Falls back to re-encoding if codecs differ.
    """
    if len(video_paths) < 2:
        raise ValueError("Need at least 2 videos to concatenate")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build a temporary concat list file (ffmpeg requires this format)
    list_file = output_path.parent / f"_concat_{output_path.stem}.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for vp in video_paths:
            # ffmpeg concat demuxer needs forward slashes + escaped quotes
            safe = str(Path(vp).resolve()).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    cmd = [
        get_ffmpeg(),
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",                 # no re-encoding (fast)
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # If codecs differ, re-encode
    if result.returncode != 0:
        cmd_reencode = [
            get_ffmpeg(), "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k",
            str(output_path),
        ]
        result = subprocess.run(cmd_reencode, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed:\n{result.stderr[-500:]}")

    # Cleanup
    try: list_file.unlink()
    except Exception: pass

    if not output_path.exists():
        raise RuntimeError(f"ffmpeg ran but {output_path} doesn't exist")
    return output_path


def is_ffmpeg_available() -> bool:
    """Check if ffmpeg is callable."""
    try:
        result = subprocess.run(
            [get_ffmpeg(), "-version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


if __name__ == "__main__":
    print(f"ffmpeg path  : {get_ffmpeg()}")
    print(f"ffmpeg works : {is_ffmpeg_available()}")
