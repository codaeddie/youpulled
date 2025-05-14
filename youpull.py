import os
import sys
import yt_dlp
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Optional: import pyannote only if diarization is enabled
try:
    from pyannote.audio import Pipeline as PyannotePipeline
except ImportError:
    PyannotePipeline = None

TRANSCRIPT_DIR = os.path.join('API', 'transcript')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("youpull")

load_dotenv()

class YouPull:
    def __init__(self, openai_api_key, use_diarization=True, diarization_token=None):
        self.openai_api_key = openai_api_key
        self.use_diarization = use_diarization
        self.diarization_token = diarization_token or os.getenv("PYANNOTE_TOKEN")
        self.client = OpenAI(api_key=openai_api_key)
        self.diarization_pipeline = None
        if self.use_diarization and PyannotePipeline:
            if not self.diarization_token:
                logger.warning("Diarization enabled but no pyannote token provided. Disabling diarization.")
                self.use_diarization = False
            else:
                self.diarization_pipeline = PyannotePipeline.from_pretrained(
                    "pyannote/speaker-diarization@2.1",
                    use_auth_token=self.diarization_token
                )
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

    def fetch_playlist_videos(self, playlist_url):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            entries = info.get('entries', [])
            videos = []
            for entry in entries:
                if entry.get('url'):
                    videos.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                        'upload_date': entry.get('upload_date'),
                        'duration': entry.get('duration'),
                    })
            return videos

    def select_videos(self, videos):
        print("\nAvailable videos:")
        for idx, v in enumerate(videos):
            print(f"[{idx+1}] {v['title']} ({v.get('upload_date', 'N/A')})")
        print("[A]ll, [Q]uit")
        selection = input("Select videos to process (e.g. 1,3,5 or A): ").strip().lower()
        if selection == 'a':
            return videos
        if selection == 'q':
            sys.exit(0)
        indices = [int(x)-1 for x in selection.split(',') if x.isdigit() and 0 < int(x) <= len(videos)]
        return [videos[i] for i in indices]

    def download_audio(self, video_url, out_dir="/tmp"):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(out_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_path = os.path.join(out_dir, f"{info['id']}.wav")
            return audio_path, info

    def transcribe(self, audio_path, language='en'):
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json"
            )
        return transcript

    def diarize(self, audio_path):
        if not self.diarization_pipeline:
            raise RuntimeError("Diarization pipeline not initialized.")
        diarization = self.diarization_pipeline(audio_path)
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'speaker': speaker,
                'start': turn.start,
                'end': turn.end
            })
        return segments

    def save_transcript(self, video, transcript, diarization_segments=None):
        title = video['title'].replace('/', '_').replace('\\', '_')
        filename = os.path.join(TRANSCRIPT_DIR, f"script_{title}.md")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {video['title']}\n")
            f.write(f"Date: {video.get('upload_date', 'N/A')}\n")
            f.write(f"Duration: {video.get('duration', 'N/A')} seconds\n\n")
            if diarization_segments:
                f.write("## Speaker Segments\n")
                for seg in diarization_segments:
                    f.write(f"- Speaker {seg['speaker']}: {seg['start']:.2f}s - {seg['end']:.2f}s\n")
                f.write("\n")
            f.write("## Transcript\n\n")
            if hasattr(transcript, 'text'):
                f.write(transcript.text)
            elif isinstance(transcript, dict) and 'text' in transcript:
                f.write(transcript['text'])
            else:
                f.write(str(transcript))
        logger.info(f"Transcript saved: {filename}")
        return filename

    def process(self, playlist_url, batch_size=3):
        videos = self.fetch_playlist_videos(playlist_url)
        if not videos:
            logger.error("No videos found in playlist.")
            return
        selected = self.select_videos(videos)
        for video in tqdm(selected, desc="Processing videos"):
            try:
                logger.info(f"Processing: {video['title']}")
                audio_path, info = self.download_audio(video['url'])
                transcript = self.transcribe(audio_path)
                diarization_segments = None
                if self.use_diarization and self.diarization_pipeline:
                    diarization_segments = self.diarize(audio_path)
                self.save_transcript(video, transcript, diarization_segments)
                os.remove(audio_path)
            except Exception as e:
                logger.error(f"Failed to process {video['title']}: {e}")
                continue

def main():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: Please set your OPENAI_API_KEY in a .env file.")
        sys.exit(1)
    use_diarization = input("Enable diarization? (y/n): ").strip().lower() == 'y'
    diarization_token = os.getenv("PYANNOTE_TOKEN") if use_diarization else None
    playlist_url = input("Enter YouTube playlist or channel URL: ").strip()
    puller = YouPull(openai_api_key, use_diarization=use_diarization, diarization_token=diarization_token)
    puller.process(playlist_url)

if __name__ == "__main__":
    main() 