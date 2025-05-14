# YouPull

Batch YouTube Speech-to-Text (ASR) & Speaker Diarization Tool

---

## Overview
YouPull is a CLI tool for batch-downloading YouTube videos (e.g., podcasts), transcribing them with OpenAI Whisper, and optionally performing speaker diarization with pyannote.audio. Each episode is saved as a Markdown document with title, date, duration, and (if enabled) speaker segments.

---

## Requirements
- Python 3.9+
- [OpenAI API key](https://platform.openai.com/account/api-keys)
- [Hugging Face token](https://huggingface.co/settings/tokens) (for diarization with pyannote.audio)
- FFmpeg (for audio extraction, usually installed with yt-dlp)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Setup
1. **Create a `.env` file in your project root:**
   ```
   OPENAI_API_KEY=sk-...
   PYANNOTE_TOKEN=hf_...   # Only needed if using diarization
   ```

2. **(Optional) Install FFmpeg:**
   - On Ubuntu: `sudo apt-get install ffmpeg`
   - On Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html)

---

## Usage
Run the CLI tool:
```bash
python youpull.py
```

- **Enable diarization? (y/n):**
  - Type `y` to use pyannote.audio for speaker diarization (requires Hugging Face token)
  - Type `n` for transcription only
- **Enter YouTube playlist or channel URL:**
  - Paste your playlist/channel URL
- **Select videos to process:**
  - Type `A` for all, or enter numbers (e.g., `1,3,5`) for specific episodes

---

## Output
- Transcripts are saved in: `API/transcript/script_<video_title>.md`
- Each file includes:
  - Title, date, duration
  - Speaker segments (if diarization enabled)
  - Full transcript

---

## Troubleshooting
- **Missing API key:** Ensure `.env` contains `OPENAI_API_KEY` (and `PYANNOTE_TOKEN` if using diarization)
- **FFmpeg errors:** Make sure FFmpeg is installed and in your PATH
- **pyannote.audio errors:** Check your Hugging Face token and internet connection
- **Rate limits:** Whisper API has usage limits; see [OpenAI docs](https://platform.openai.com/docs/guides/rate-limits)

---

## Best Practices for Diarization Benchmarking
- Use high-quality audio for best diarization results
- Review diarization output for accuracy (speaker turns, labels)
- Test on a variety of podcast types for benchmarking

---

## License
MIT
