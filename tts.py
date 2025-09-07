import asyncio
import pyttsx3
from concurrent.futures import ThreadPoolExecutor

Assistant = pyttsx3.init('sapi5')
voices = Assistant.getProperty('voices')
Assistant.setProperty('voice', voices[1].id)
Assistant.setProperty('rate', 190)

# Blocking speak function
def speak(audio):
    print("   ")
    print(f":{audio}")
    Assistant.say(audio)
    Assistant.runAndWait()

# Async wrapper
# async def speak(audio):
#     loop = asyncio.get_event_loop()
#     await loop.run_in_executor(None, speak_sync, audio)

if __name__ == "__main__":
    speak("I'm Om, your AI assistant")