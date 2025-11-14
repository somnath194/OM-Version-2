"""
Voice Chatbot with STT, LLM, and TTS
MVP Version: Streaming typing effect, then speak complete response
"""

import asyncio
import websockets
import base64
import json
import time
import subprocess
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import pvporcupine
from pvrecorder import PvRecorder
from collections import deque
import struct
import re


# ============================================================================
# CONFIGURATION
# ============================================================================

# Sleep/Wake parameters
SLEEP_TIMEOUT = 180  # 3 minutes in seconds
WAKE_WORDS = ['wake up nandi', 'nandi lets work', 'nandi let\'s work', 'wake up']
SLEEP_WORDS = ['go to sleep', 'sleep now', 'goodbye nandi', 'nandi sleep']

# Wake word detection parameters
WAKE_WORD_PATTERNS = ['hey nandi', 'hey nandy', 'a nandi', 'hey nandi,', 'hey nandi.']
PRE_WAKE_BUFFER_SECONDS = 1.5
POST_WAKE_CAPTURE_SECONDS = 5.0
WAKE_WORD_COOLDOWN = 5.0
STT_RESPONSE_TIMEOUT = 8.0

# TTS parameters
TTS_MODEL = "tts-1"
TTS_VOICE = "alloy"


# ============================================================================
# SIMPLE TTS MODULE
# ============================================================================

class SimpleTTSPlayer:
    """Simple TTS player - speaks complete text at once"""
    
    def __init__(self, client: AsyncOpenAI, model: str = TTS_MODEL, voice: str = TTS_VOICE):
        self.client = client
        self.model = model
        self.voice = voice
        self.is_playing = False
    
    def _start_new_ffplay(self):
        """Start a fresh ffplay process ready to receive audio"""
        try:
            process = subprocess.Popen(
                [
                    "ffplay",
                    "-nodisp",
                    "-autoexit",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-"
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return process
        except Exception as e:
            print(f"❌ Failed to start ffplay: {e}")
            return None
    
    async def speak(self, text: str) -> bool:
        """Speak complete text"""
        if not text.strip():
            return False
        
        self.is_playing = True
        start_time = time.time()
        
        try:
            print(f"\n🔊 Speaking complete response...")
            
            ffplay = self._start_new_ffplay()
            if not ffplay:
                return False
            
            async with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=4096):
                    if ffplay.stdin:
                        ffplay.stdin.write(chunk)
                        ffplay.stdin.flush()
            
            if ffplay.stdin:
                ffplay.stdin.close()
            
            ffplay.wait()
            
            total_time = (time.time() - start_time) * 1000
            print(f"   ✓ Spoken in {total_time:.0f}ms\n")
            return True

        except Exception as e:
            print(f"❌ TTS Error: {str(e)}")
            if ffplay and ffplay.poll() is None:
                ffplay.kill()
            return False
        finally:
            self.is_playing = False


# ============================================================================
# STREAMING LLM MODULE (TYPE EFFECT ONLY)
# ============================================================================

class StreamingLLMAgent:
    """Language Model Agent with streaming support"""

    def __init__(self, ws_uri="ws://127.0.0.1:8000/ws/chat_stream", session_id="voice-session"):
        self.ws_uri = ws_uri
        self.session_id = session_id
        self.ws = None
        self.is_connecting = False
        self.lock = asyncio.Lock()

    async def initialize(self):
        """Initialize or reinitialize the persistent WebSocket connection"""
        async with self.lock:
            if self.is_connecting:
                return
            self.is_connecting = True
            try:
                if self.ws is None or self.ws.state == websockets.protocol.State.CLOSED:
                    print(f"🟢 Establishing streaming connection to {self.ws_uri}")
                    self.ws = await websockets.connect(
                        self.ws_uri, 
                        ping_interval=20, 
                        ping_timeout=20,
                        close_timeout=5
                    )
            except Exception as e:
                print(f"❌ Failed to connect to WebSocket: {e}")
                self.ws = None
            finally:
                self.is_connecting = False

    async def close(self):
        """Close the persistent WebSocket connection"""
        async with self.lock:
            if self.ws and self.ws.state != websockets.protocol.State.CLOSED:
                await self.ws.close()
                self.ws = None

    async def process_stream(self, user_input: str, callback):
        """
        Process user input through WebSocket with streaming
        callback(token) is called for each token
        Returns final response
        """
        await self.initialize()
        
        if self.ws is None or self.ws.state == websockets.protocol.State.CLOSED:
            return "Sorry, I couldn't connect to the backend."

        try:
            payload = {"query": user_input, "session_id": self.session_id}
            await self.ws.send(json.dumps(payload))

            final_response = ""
            
            while True:
                response = await asyncio.wait_for(self.ws.recv(), timeout=30)
                
                try:
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    if msg_type == "stream":
                        token = data.get("token", "")
                        if token:
                            await callback(token)
                    
                    elif msg_type == "end":
                        final_response = data.get("response", "")
                        break
                    
                    elif "error" in data:
                        print(f"❌ Server error: {data['error']}")
                        return "Sorry, there was an error."
                
                except json.JSONDecodeError:
                    continue

            return final_response or "Sorry, I got an empty response."

        except asyncio.TimeoutError:
            print("❌ WebSocket timeout")
            await self.close()
            return "Sorry, the connection timed out."
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"❌ WS closed unexpectedly: {e}")
            await self.close()
            return "Connection closed unexpectedly."
        except Exception as e:
            print(f"❌ LLM WS Error: {e}")
            await self.close()
            return "Sorry, I encountered a connection error."


# ============================================================================
# VOICE CLIENT MODULE
# ============================================================================

class VoiceClient:
    """Voice client with streaming typing effect, then TTS"""
    
    def __init__(self, server_url: str, openai_client: AsyncOpenAI):
        self.server_url = server_url
        self.websocket = None
        
        # State management
        self.is_sleeping = False
        self.last_activity_time = time.time()
        
        # Wake word detection state
        self.waiting_for_stt_response = False
        self.stt_request_time = 0
        self.last_wake_detection_time = 0
        self.current_command_id = 0
        self.last_interim_transcription = ""
        self.interim_transcription_time = 0
        
        # Components
        self.tts = SimpleTTSPlayer(openai_client)
        self.llm = StreamingLLMAgent()
        
        # Porcupine setup
        self.porcupine = pvporcupine.create(
            access_key=os.getenv("PICOVOICE_ACCESS_KEY"),
            keyword_paths=["D:\\Programs\\om_python_client\\hey-nandi_en_windows_v3_0_0.ppn"]
        )
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        
        # Circular buffer for pre-wake audio
        buffer_frames = int(16000 / self.porcupine.frame_length) * int(PRE_WAKE_BUFFER_SECONDS)
        self.pre_wake_buffer = deque(maxlen=buffer_frames)
        
    def strip_wake_word(self, text: str) -> str:
        """Remove wake word patterns from transcription"""
        text_lower = text.lower().strip()
        
        for pattern in WAKE_WORD_PATTERNS:
            if text_lower.startswith(pattern):
                text = text[len(pattern):].strip()
                text = re.sub(r'^[,.\s]+', '', text)
                break
            text = re.sub(rf'\b{re.escape(pattern)}\b', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def check_for_sleep_word(self, transcription: str) -> bool:
        """Check if transcription contains a sleep word"""
        if not transcription:
            return False
        transcription_lower = transcription.lower().strip()
        return any(sleep_word in transcription_lower for sleep_word in SLEEP_WORDS)
    
    async def enter_sleep_mode(self):
        """Enter sleep mode"""
        if not self.is_sleeping:
            self.is_sleeping = True
            print("\n💤 Entering sleep mode...")
            await self.tts.speak("Going to sleep. Say Hey Nandi to wake me up.")
    
    async def wake_up(self):
        """Wake from sleep mode"""
        if self.is_sleeping:
            self.is_sleeping = False
            self.last_activity_time = time.time()
            print("\n✨ Waking up!")
            await self.tts.speak("I'm awake and ready to help!")

    async def capture_and_listen(self):
        """Main audio capture loop - listens for wake word and captures command"""
        print("👂 Listening for wake word 'Hey Nandi'...\n")
        self.recorder.start()
        
        post_wake_buffer = []
        is_capturing_command = False
        frames_to_capture = 0
        
        while True:
            try:
                pcm = self.recorder.read()
                self.pre_wake_buffer.append(pcm)
                current_time = time.time()
                
                # Check if STT response has timed out
                if self.waiting_for_stt_response:
                    time_waiting = current_time - self.stt_request_time
                    if time_waiting > STT_RESPONSE_TIMEOUT:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"⏰ [{timestamp}] STT response timeout ({time_waiting:.1f}s) - resetting state")
                        
                        if self.last_interim_transcription and (current_time - self.interim_transcription_time) < 5:
                            print(f"💡 [{timestamp}] Using last interim transcription as fallback")
                            command = self.strip_wake_word(self.last_interim_transcription)
                            if command:
                                print(f"[{timestamp}] 🎯 Command (interim): {command}")
                                asyncio.create_task(self.process_and_respond(command, timestamp))
                        
                        self.waiting_for_stt_response = False
                        self.stt_request_time = 0
                        self.last_interim_transcription = ""
                        self.pre_wake_buffer.clear()
                        print(f"🧹 [{timestamp}] Audio buffer cleared")
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0 and not is_capturing_command:
                    if current_time - self.last_wake_detection_time < WAKE_WORD_COOLDOWN:
                        continue
                    
                    if self.waiting_for_stt_response:
                        time_waiting = current_time - self.stt_request_time
                        print(f"⏳ Still processing previous command (waiting {time_waiting:.1f}s)...")
                        continue
                    
                    self.last_wake_detection_time = current_time
                    self.current_command_id += 1
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    print(f"🪄 [{timestamp}] Wake word detected! (ID: {self.current_command_id})")
                    
                    is_capturing_command = True
                    frames_to_capture = int(16000 / self.porcupine.frame_length) * POST_WAKE_CAPTURE_SECONDS
                    post_wake_buffer.clear()
                    continue
                
                if is_capturing_command:
                    post_wake_buffer.append(pcm)
                    frames_to_capture -= 1
                    
                    if frames_to_capture <= 0:
                        all_frames = list(self.pre_wake_buffer) + post_wake_buffer
                        raw_audio = b''.join(struct.pack("h" * len(f), *f) for f in all_frames)
                        
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"📤 [{timestamp}] Sending audio to STT (ID: {self.current_command_id})")
                        
                        self.waiting_for_stt_response = True
                        self.stt_request_time = current_time
                        await self.send_audio_to_stt(raw_audio, self.current_command_id)
                        
                        is_capturing_command = False
                        post_wake_buffer.clear()
                
                if not self.is_sleeping and not is_capturing_command:
                    if current_time - self.last_activity_time > SLEEP_TIMEOUT:
                        await self.enter_sleep_mode()
                
                await asyncio.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Error in capture loop: {e}")
                await asyncio.sleep(0.1)

    async def send_audio_to_stt(self, raw_audio: bytes, command_id: int):
        """Send audio to STT websocket"""
        try:
            base64_audio = base64.b64encode(raw_audio).decode("utf-8")
            payload = {
                "clientType": "react",
                "audio": base64_audio,
                "commandId": command_id
            }
            await self.websocket.send(json.dumps(payload)) # type: ignore
        except Exception as e:
            print(f"❌ Error sending to STT: {e}")
            self.waiting_for_stt_response = False

    async def receive_and_process(self):
        """Receive STT transcriptions and process commands"""
        try:
            async for message in self.websocket: # type: ignore
                try:
                    data = json.loads(message)
                    
                    if 'transcription' not in data:
                        continue
                    
                    transcription = data['transcription']
                    status = data.get('status', 'unknown')
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if not transcription:
                        continue
                    
                    self.last_activity_time = time.time()
                    
                    status_icon = "✓" if status == "confirmed" else "..."
                    print(f"[{timestamp}] {status_icon} {transcription}")
                    
                    if status != "confirmed" and self.waiting_for_stt_response:
                        self.last_interim_transcription = transcription
                        self.interim_transcription_time = time.time()
                    
                    if status == "confirmed" and self.waiting_for_stt_response:
                        response_time = time.time() - self.stt_request_time
                        self.waiting_for_stt_response = False
                        self.stt_request_time = 0
                        self.last_interim_transcription = ""
                        
                        print(f"[{timestamp}] ⏱️  STT response received in {response_time:.1f}s")
                        
                        command = self.strip_wake_word(transcription)
                        
                        if not command:
                            print(f"[{timestamp}] ⚠️  No command detected (only wake word)")
                            continue
                        
                        print(f"[{timestamp}] 🎯 Command: {command}")
                        
                        if self.check_for_sleep_word(command):
                            await self.enter_sleep_mode()
                        else:
                            await self.process_and_respond(command, timestamp)
                    
                    elif status == "confirmed" and not self.waiting_for_stt_response:
                        print(f"[{timestamp}] ℹ️  Received unexpected confirmed transcription (ignoring)")
                
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("❌ Connection closed by server")
        except Exception as e:
            print(f"❌ Error in receive loop: {e}")

    async def process_and_respond(self, command: str, timestamp: str):
        """
        Process command with streaming LLM
        1. Show typing effect as tokens arrive
        2. After complete, speak the full response
        """
        try:
            print(f"\n🤖 [{timestamp}] Processing: {command}")
            llm_start = time.time()
            
            # Track streaming progress
            token_count = 0
            collected_response = ""
            
            print(f"🤖 [{timestamp}] Response: ", end="", flush=True)
            
            async def token_callback(token: str):
                nonlocal token_count, collected_response
                token_count += 1
                collected_response += token
                # Print with typing animation effect
                print(token, end="", flush=True)
            
            # Stream response from LLM (just typing effect)
            final_response = await self.llm.process_stream(command, token_callback)
            
            llm_time = (time.time() - llm_start) * 1000
            print(f"\n🤖 [{timestamp}] Complete ({llm_time:.0f}ms, {token_count} tokens)")
            
            # Now speak the COMPLETE response
            if final_response:
                await self.tts.speak(final_response)
            
        except Exception as e:
            print(f"\n❌ Error processing command: {e}")
            await self.tts.speak("Sorry, I encountered an error.")

    async def connect_and_run(self):
        """Main connection loop"""
        while True:
            try:
                print(f"🔌 Connecting to STT server at {self.server_url}...")
                async with websockets.connect(self.server_url) as websocket:
                    self.websocket = websocket
                    print("✅ Connected to STT server\n")
                    
                    await websocket.send(json.dumps({"clientType": "react"}))
                    
                    self.last_activity_time = time.time()
                    
                    await asyncio.gather(
                        self.capture_and_listen(),
                        self.receive_and_process()
                    )
                    
            except websockets.exceptions.ConnectionClosed:
                print("\n❌ Connection closed. Reconnecting in 5 seconds...")
            except Exception as e:
                print(f"\n❌ Connection error: {e}")
                print("Reconnecting in 5 seconds...")
            finally:
                await asyncio.sleep(5)
    
    def cleanup(self):
        """Cleanup resources"""
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
            self.recorder.delete()
        if self.porcupine:
            self.porcupine.delete()
        print("\n👋 Client stopped")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    load_dotenv(dotenv_path=".env", override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return
    
    openai_client = AsyncOpenAI(api_key=api_key)
    server_url = os.getenv("WEBSOCKET_SERVER_URL", "ws://localhost:8100")
    client = VoiceClient(server_url=server_url, openai_client=openai_client)
    
    try:
        await client.connect_and_run()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping client...")
    finally:
        client.cleanup()


if __name__ == "__main__":
    print("=" * 70)
    print("🎙️  VOICE CHATBOT MVP - Type Effect + TTS")
    print("=" * 70)
    print(f"⏰ Auto-sleep timeout: {SLEEP_TIMEOUT}s ({SLEEP_TIMEOUT/60:.1f} minutes)")
    print(f"🔊 Wake word: 'Hey Nandi'")
    print(f"💤 Sleep commands: {', '.join(SLEEP_WORDS)}")
    print(f"📝 Streaming: Type effect only, then speak complete response")
    print(f"🔊 TTS: {TTS_MODEL} ({TTS_VOICE})")
    print("=" * 70)
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")