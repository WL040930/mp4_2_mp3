---
title: MP4 to MP3 Converter
emoji: 🎵
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7680
pinned: false
---

# mp4_2_mp3

Convert MP4 video files to MP3 audio files easily.

## Overview

This repository provides a simple web application for converting video files (MP4, MKV, AVI, etc.) to MP3 audio format. It uses MoviePy for audio extraction and provides a user-friendly web interface for batch conversions.

## Features

- Convert multiple video files to MP3 simultaneously
- Web-based interface with progress tracking
- Supports various video formats: MP4, MKV, AVI, MOV, FLV, WMV, M4V
- Batch processing with ZIP download
- Error reporting for failed conversions
- No local installation required

## Technologies

- **Backend**: Python Flask
- **Audio Processing**: MoviePy
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Docker (compatible with Hugging Face Spaces)

## Local Development

### Prerequisites

- Python 3.12+
- FFmpeg (for MoviePy)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/WL040930/mp4_2_mp3.git
   cd mp4_2_mp3
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python -m src.web_app
   ```

4. Open http://localhost:7680 in your browser.

### Docker

Build and run with Docker:
```bash
docker build -t mp4-2-mp3 .
docker run -p 7680:7680 mp4-2-mp3
```

## Hugging Face Spaces Deployment

This app is designed to run on Hugging Face Spaces using Docker.

### Deploying to Spaces

1. Fork this repository to your GitHub account.
2. Go to [Hugging Face Spaces](https://huggingface.co/spaces).
3. Create a new Space with Docker as the SDK.
4. Connect your forked repository.
5. The Space will automatically build and deploy using the provided Dockerfile.

### Space Configuration

- **Space Type**: Docker
- **Hardware**: CPU Basic (or higher for faster processing)
- **Persistent Storage**: Not required
- **Secrets**: None needed

## Usage

1. Upload one or more video files.
2. Click "Convert" to start the conversion process.
3. Monitor progress in real-time.
4. Download the ZIP file containing all converted MP3 files.

## API

The web app provides a REST API for programmatic access:

- `POST /convert`: Upload files and start conversion
- `GET /status/<job_id>`: Check conversion status
- `GET /download/<job_id>`: Download results

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source. Please check the license file for details.
