import requests
import threading
import asyncio
import aiohttp
import time
import pygetwindow as gw
from flags import exit_event,exit_commands,sleep_commands,wake_up_commands
from stt import run as run_flask
from brain import brain_function,chat_history
from tts import speak
import json
from command_executor import CommandExecutor

file_path = "D:\\Programs\\OM-Version-2\\SpeechRecogonisition.txt"

# Constants for sleep/wake
SLEEP_TIMEOUT = 180  # 3 minutes in seconds

# States
is_awake = True
last_command_time = time.time()
executor = CommandExecutor()
last_transcript = ""

def close_chrome():
    app_name = "Google Chrome"
    l = []
    data = gw.getAllTitles()
    for i in data:
        if app_name in i:
            app_instance = gw.getWindowsWithTitle(i)[0]
            app_instance.close()

def wait_and_shutdown():
    exit_event.wait()
    close_chrome()
    requests.post('http://localhost:5000/shutdown')

async def handle_response(response_json):
    conversation_output = None
    function_actions = []
    for item in response_json:
        if "converssion_output" in item:
            conversation_output = item["converssion_output"]
        elif item.get("action"):
            function_actions.append(item)

    return conversation_output, function_actions


async def assistant_loop():
    global is_awake, last_command_time, last_transcript

    speak("System is Ready to Take Commands.....")

    while not exit_event.is_set():
        await asyncio.sleep(1)

        with open(file_path, "r") as file:
            transcript = file.read().strip().lower()
        # Reset transcript file
        open(file_path, "w").close()

        # Skip empty transcript
        if not transcript or transcript == last_transcript:
            # Check for inactivity sleep
            if is_awake and time.time() - last_command_time > SLEEP_TIMEOUT:
                await speak("No command for 3 minutes. Going to sleep mode...")
                is_awake = False
            continue


        # Global exit
        if transcript in exit_commands:
            exit_event.set()
            speak("Shutting down...")
            print(chat_history)
            break

        # Manual sleep command
        if transcript in sleep_commands:
            if is_awake:
                is_awake = False
                speak("Going to sleep...")
            else:
                speak("I'm Already Sleeping!")
            continue

        # Wake up command
        if transcript in wake_up_commands:
            if not is_awake:
                is_awake = True
                last_command_time = time.time()
                speak("I am awake now!")
            else:
                speak("I'm Already Awake Ready for Your Commands......")
            continue

        # If awake, parse and execute command
        if is_awake and transcript != last_transcript:
            last_command_time = time.time()
            last_transcript = transcript

            response = await brain_function(transcript)
            # print(response)

            conv_output, actions = await handle_response(json.loads(response))
            speak(conv_output)
            action_results = await executor.execute(actions)
            # print(f"Action results: {action_results}")

            if action_results:
                result_context = f"Action results: {action_results}"
                followup_response = await brain_function(f"{conv_output}\n{result_context}")
                followup_conv_output, _ = await handle_response(json.loads(followup_response))
                speak(followup_conv_output)

            # print(actions)

        if not is_awake:
            speak("I'm Sleeping... Waiting for wake-up command.")


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=wait_and_shutdown, daemon=True).start()
    asyncio.run(assistant_loop())
