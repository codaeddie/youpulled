# YouPull - Local Version

YouTube ASR with full speaker diarization running on your hardware.

## Prerequisites

- Python 3.9+
- ffmpeg installed
- Optional: CUDA-capable GPU (falls back to CPU)

## Installation

```bash
pip install -r requirements.txt
```

## Core Components

### 1. YouTube Downloader
- Uses `yt-dlp` for reliable downloads
- Extracts audio only (saves space/time)
- Handles playlists and single videos

### 2. ASR Engine
- `faster-whisper` for transcription
- Model sizes: tiny, base, small, medium, large-v2
- Auto-detects GPU/CPU

### 3. Speaker Diarization
- `pyannote.audio` for speaker separation
- Requires HuggingFace token for models
- Outputs speaker-labeled segments

### 4. Processing Pipeline
```
YouTube URL → Download audio → Transcribe → Diarize → Format output
```

## Usage

```python
from youpull import YouPullLocal

# Initialize
puller = YouPullLocal(
    whisper_model="base",
    device="cuda"  # or "cpu"
)

# Process playlist
results = puller.process_playlist(
    url="https://youtube.com/playlist?list=...",
    output_dir="./transcripts"
)

# Process single video
result = puller.process_video(
    url="https://youtube.com/watch?v=...",
    output_path="./transcript.json"
)
```

## Output Format

```json
{
    "title": "Podcast Title",
    "date": "2024-01-01",
    "duration": 3600,
    "speakers": ["Speaker A", "Speaker B"],
    "segments": [
        {
            "speaker": "Speaker A",
            "start": 0.0,
            "end": 15.5,
            "text": "Hello and welcome to the podcast"
        }
    ]
}
```

## Performance

- Base model on CPU: ~10x realtime
- Base model on GPU: ~50x realtime
- Large model on GPU: ~15x realtime

## Limitations

- First run downloads models (~1-2GB)
- Diarization accuracy varies with audio quality
- CPU processing is slow for long podcasts

## Configuration

Create `config.yaml`:

```yaml
whisper:
  model: "base"
  language: "en"
  
diarization:
  min_speakers: 2
  max_speakers: 5
  
output:
  format: "json"  # or "txt", "vtt"
  include_timestamps: true
```
