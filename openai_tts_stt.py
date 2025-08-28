from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os

# Load API key
load_dotenv(dotenv_path=".env", override=True)
api_key = os.getenv("OPENAI_API_KEY")

# Initialize model
client = OpenAI(api_key=api_key)  # type: ignore


response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",  # choose from their presets
    input="Hello, how are you today?"
)

speech_path = Path("output.mp3")
response.stream_to_file(speech_path)
print("Audio saved to:", speech_path)

audio_file = open("testing_files//Recording (5).wav", "rb")

# Speech to text (transcribe same language)
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file
)

print("Transcription:", transcript.text)