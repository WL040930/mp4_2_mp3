import os
from pathlib import Path
from typing import Any, Iterable

_moviepy_import_error = None
try:
    from moviepy import VideoFileClip  # type: ignore[import]
except (ModuleNotFoundError, ImportError) as exc:
    try:
        from moviepy.editor import VideoFileClip  # type: ignore[import]
    except (ModuleNotFoundError, ImportError):
        _moviepy_import_error = exc
        VideoFileClip = None  # type: ignore[assignment]

VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".m4v")


def _require_moviepy() -> None:
    if VideoFileClip is None:
        raise ModuleNotFoundError(
            "moviepy is required to convert videos. Install it with `pip install moviepy`."
        ) from _moviepy_import_error


def video_to_audio_file(
    video_path: os.PathLike | str,
    audio_path: os.PathLike | str,
    *,
    logger: Any | None = None,
) -> Path:
    """
    Convert a single video file to an audio file.

    :param video_path: Path to the video file.
    :param audio_path: Path where the audio file will be written.
    :return: Path to the generated audio file.
    """
    _require_moviepy()

    video_path = Path(video_path)
    audio_path = Path(audio_path)
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    with VideoFileClip(str(video_path)) as video:
        if video.audio is None:
            raise ValueError(f"Video '{video_path.name}' has no audio track")
        video.audio.write_audiofile(str(audio_path), logger=logger)

    return audio_path


def _iter_video_files(folder: Path, suffixes: Iterable[str]) -> Iterable[Path]:
    suffixes = tuple(ext.lower() for ext in suffixes)
    for candidate in folder.iterdir():
        if candidate.is_file() and candidate.suffix.lower() in suffixes:
            yield candidate


def video_to_audio_folder(
    video_folder: os.PathLike | str,
    output_folder: os.PathLike | str | None = None,
    audio_format: str = "mp3",
) -> list[Path]:
    """
    Convert all supported video files in a folder to audio files.

    :param video_folder: Path to the folder containing videos.
    :param output_folder: Path to save audio files. If None, audio files are saved alongside the videos.
    :param audio_format: Audio output format, default is mp3.
    :return: List of generated audio file paths.
    """
    _require_moviepy()

    video_folder_path = Path(video_folder)
    output_folder_path = Path(output_folder) if output_folder else video_folder_path
    output_folder_path.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for video_path in _iter_video_files(video_folder_path, VIDEO_EXTENSIONS):
        audio_name = f"{video_path.stem}.{audio_format}"
        audio_path = output_folder_path / audio_name

        print(f"Converting: {video_path.name} → {audio_name}")
        try:
            generated.append(video_to_audio_file(video_path, audio_path))
        except Exception as exc:
            print(f"Failed to convert {video_path.name}: {exc}")

    if generated:
        print("✅ Conversion completed!")
    else:
        print("ℹ️ No compatible video files found.")

    return generated

# Example usage:
# Paths based on your folders
if __name__ == "__main__":
    video_folder = r"/Volumes/Expansion/YYC WS/WSA/22,23 August 2025/23 August/Rendered"
    output_folder = r"/Users/wl/Documents/book/mp3"
    video_to_audio_folder(video_folder, output_folder)
