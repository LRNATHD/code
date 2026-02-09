
import subprocess
import os

cmd = [
    'yt-dlp',
    '--extract-audio',
    '--audio-format', 'mp3',
    '--audio-quality', '0',
    # Use the generated cookies.txt
    '--cookies', 'cookies.txt',
    # We still need the android client trick usually?
    '--extractor-args', 'youtube:player_client=android',
    'https://music.youtube.com/watch?v=LO0BRuBFtp0'
]

print("Running test download with generated cookies.txt...")
try:
    subprocess.run(cmd, check=True)
    print("Download successful!")
except subprocess.CalledProcessError as e:
    print(f"Download failed with error: {e}")
