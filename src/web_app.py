"""Simple web interface for converting video files to audio."""

from __future__ import annotations

import shutil
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from flask import (
    Flask,
    abort,
    after_this_request,
    jsonify,
    render_template,
    request,
    send_file,
    url_for,
)
from proglog import ProgressBarLogger

from mp4_2_mp3 import VIDEO_EXTENSIONS, video_to_audio_file

app = Flask(
    __name__,
    template_folder=str(Path(__file__).with_name("templates")),
)


@dataclass
class ConversionJob:
    id: str
    status: str = "pending"
    total_files: int = 0
    converted: int = 0
    processed_files: int = 0
    errors: list[str] = field(default_factory=list)
    message: str | None = None
    download_path: Path | None = None
    temp_dir: Path | None = None
    generated_files: list[str] = field(default_factory=list)
    unsupported_files: list[str] = field(default_factory=list)
    current_file: str | None = None
    current_progress: int = 0


jobs: dict[str, ConversionJob] = {}
jobs_lock = threading.Lock()

ALLOWED_SUFFIXES = {suffix.lower() for suffix in VIDEO_EXTENSIONS}


def _sanitize_relative_path(filename: str) -> Path:
    candidate = Path(filename)
    safe_parts = [part for part in candidate.parts if part not in ("", ".", "..")]
    if not safe_parts:
        return Path(candidate.name or "uploaded_file")
    return Path(*safe_parts)


def _filter_supported(files: Iterable[Path]) -> list[Path]:
    return [path for path in files if path.suffix.lower() in ALLOWED_SUFFIXES]


def _update_job(job_id: str, **changes) -> None:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return
        for key, value in changes.items():
            setattr(job, key, value)


class JobProgressLogger(ProgressBarLogger):
    """Bridge MoviePy progress callbacks back to the job tracker."""

    def __init__(self, job_id: str) -> None:
        super().__init__()
        self.job_id = job_id

    def callback(self, **changes) -> None:  # type: ignore[override]
        super().callback(**changes)

        bar = None
        for key in ("chunk", "chunks", "t"):
            candidate = self.bars.get(key)
            if candidate:
                bar = candidate
                break

        if not bar:
            return

        fraction = bar.get("fraction")
        if fraction is None:
            total = bar.get("total") or bar.get("n") or 0
            completed = bar.get("index")
            if completed is None:
                completed = bar.get("value")
            if completed is None:
                completed = bar.get("current")
            if total and completed is not None:
                fraction = completed / total

        if fraction is None:
            return

        percent = max(0, min(100, int(round(float(fraction) * 100))))
        _update_job(self.job_id, current_progress=percent)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/convert")
def convert():
    uploads = request.files.getlist("videos")
    if not uploads or all(upload.filename == "" for upload in uploads):
        return (
            jsonify({"error": "Please choose at least one video file or folder."}),
            400,
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="convert_job_"))
    upload_dir = temp_dir / "uploads"
    output_dir = temp_dir / "outputs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []
    for storage in uploads:
        if not storage.filename:
            continue
        relative_path = _sanitize_relative_path(storage.filename)
        destination = upload_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        storage.save(destination)
        saved_files.append(destination)

    if not saved_files:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": "No files were uploaded."}), 400

    supported_files = _filter_supported(saved_files)
    if not supported_files:
        unsupported = sorted(path.relative_to(upload_dir).as_posix() for path in saved_files)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return (
            jsonify(
                {
                    "error": "No supported video files were uploaded.",
                    "details": {"Unsupported files": unsupported},
                }
            ),
            400,
        )

    job_id = str(uuid4())
    job = ConversionJob(
        id=job_id,
        total_files=len(supported_files),
        temp_dir=temp_dir,
        unsupported_files=sorted(
            path.relative_to(upload_dir).as_posix()
            for path in saved_files
            if path not in supported_files
        ),
        message="Preparing conversion...",
    )

    with jobs_lock:
        jobs[job_id] = job

    worker = threading.Thread(
        target=_process_job,
        args=(job_id, upload_dir, output_dir, supported_files),
        daemon=True,
    )
    worker.start()

    return jsonify({"job_id": job_id})


def _process_job(
    job_id: str,
    upload_dir: Path,
    output_dir: Path,
    supported_files: list[Path],
) -> None:
    errors: list[str] = []
    generated: list[tuple[Path, Path]] = []

    _update_job(
        job_id,
        status="running",
        message="Converting videos...",
        errors=[],
        current_progress=0,
    )

    for index, video_path in enumerate(supported_files, start=1):
        relative = video_path.relative_to(upload_dir)
        audio_relative = relative.with_suffix(".mp3")
        audio_path = output_dir / audio_relative

        _update_job(
            job_id,
            current_file=relative.as_posix(),
            processed_files=index - 1,
            current_progress=0,
        )

        logger = JobProgressLogger(job_id)
        success = False

        try:
            produced = video_to_audio_file(video_path, audio_path, logger=logger)
        except ModuleNotFoundError as exc:
            errors.append(str(exc))
            _update_job(
                job_id,
                status="failed",
                message=str(exc),
                errors=list(errors),
                processed_files=index,
                current_file=None,
                current_progress=0,
            )
            return
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{relative.as_posix()}: {exc}")
        else:
            generated.append((produced, audio_relative))
            _update_job(job_id, converted=len(generated))
            success = True
        finally:
            _update_job(
                job_id,
                errors=list(errors),
                processed_files=index,
                current_progress=100 if success else 0,
            )

    if not generated:
        message = (
            "Conversion failed for all uploaded videos."
            if errors
            else "No audio files were generated."
        )
        _update_job(
            job_id,
            status="failed",
            message=message,
            current_file=None,
            current_progress=0,
        )
        return

    zip_path = output_dir / "converted_audio.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zip_file:
        for audio_path, arcname in generated:
            zip_file.write(audio_path, arcname=str(arcname))
        if errors:
            report = "Some files could not be converted:\n" + "\n".join(errors)
            zip_file.writestr("conversion_report.txt", report)

    message = "Conversion completed!"
    if errors:
        message = "Conversion completed with some errors."

    _update_job(
        job_id,
        status="completed",
        message=message,
        download_path=zip_path,
        generated_files=[arcname.as_posix() for _, arcname in generated],
        current_file=None,
        current_progress=100,
    )


@app.get("/status/<job_id>")
def status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            abort(404)
        payload = {
            "job_id": job.id,
            "status": job.status,
            "message": job.message,
            "total_files": job.total_files,
            "converted": job.converted,
            "processed_files": job.processed_files,
            "errors": job.errors,
            "generated_files": job.generated_files,
            "unsupported_files": job.unsupported_files,
            "current_file": job.current_file,
            "current_progress": job.current_progress,
        }
        if job.status == "completed" and job.download_path:
            payload["download_url"] = url_for("download", job_id=job.id)
    return jsonify(payload)


@app.get("/download/<job_id>")
def download(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None or job.status != "completed" or job.download_path is None:
            abort(404)
        download_path = job.download_path
        temp_dir = job.temp_dir

    @after_this_request
    def _cleanup(response):  # type: ignore[override]
        with jobs_lock:
            jobs.pop(job_id, None)
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        return response

    return send_file(
        download_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_path.name,
    )


if __name__ == "__main__":
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
