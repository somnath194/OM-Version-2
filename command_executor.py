
import pygetwindow as gw
import paho.mqtt.client as paho
import time
import ast
import asyncio
import aiohttp
import inspect
from rapidfuzz import process
import os
import webbrowser
import pywhatkit as kit
import pyautogui
from time import sleep
import speedtest
import socket
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import json
import requests
import yt_dlp

# Changable locations of applications
# App paths, windows search locations, wled ips, any wled segment map, join api key and device id's, contact list,  

APP_WITH_PATH = {
    "Visual Studio Code": "C:\\Users\\somi\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "Google Chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "Brave": "C:\\Users\\somi\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
    "Notepad": "C:\\Windows\\System32\\notepad.exe",
    "Paint": "C:\\Users\\somi\\AppData\\Local\\Microsoft\\WindowsApps\\mspaint.exe",
    "Arduino IDE 2.3.5": "C:\\Program Files\\Arduino IDE\\Arduino IDE.exe",
    "Command Prompt": "cmd",  # Using 'cmd' since it's a system command
    "Task Manager": "taskmgr",  # System command for Task Manager
    "Settings": "ms-settings:",  # URI for Windows settings
    "File Explorer": "explorer",  # Opens File Explorer
    "DaVinci Resolve": "C:\\Users\\somi\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Blackmagic Design\\DaVinci Resolve\\DaVinci Resolve.lnk"
                }


WLED_IP = "192.168.1.5"
BACK_WLED_IP = "192.168.1.6"

join_device_id = "c6a07d0b1b9e470eb7181498d7eb8d49" #phone
join_api_key = "8680fb0ccc1249908d265c378ea0e167"

SEGMENT_MAP = {
    "front almary": 1,
    "behind the money plant": 2,
    "ceiling": 3,
    "under laptop table": 4,
    "under pc table": 5,
    "ganesha almary": 6,
    "shiva almary": 7,
    "all":8,
    "back almary": 9
}

class WindowsAutomation:
    def __init__(self):
        # Setup for volume control
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        self.join_device_id = "c6a07d0b1b9e470eb7181498d7eb8d49" # phone
        self.join_api_key = "8680fb0ccc1249908d265c378ea0e167"

    async def control_application(self, app_name, control_type, device):
        app = self.get_best_app_match(app_name)

        # Define action handlers in a dict
        def open_app():
            os.startfile(APP_WITH_PATH[app])

        def close_app():
            for title in self.search_app_windows(app):
                gw.getWindowsWithTitle(title)[0].close()

        def minimize_app():
            for title in self.search_app_windows(app):
                gw.getWindowsWithTitle(title)[0].minimize()

        def maximize_app():
            for title in self.search_app_windows(app):
                gw.getWindowsWithTitle(title)[0].maximize()

        # Action mapping
        actions = {
            "open": open_app,
            "close": close_app,
            "minimize": minimize_app,
            "maximize": maximize_app
        }

        if device == "pc":
        # Execute the action if it exists
            if control_type in actions:
                actions[control_type]()
            else:
                raise ValueError(f"Unknown control type: {control_type}")
        elif device == "phone":
            if control_type == "open":
                open_app_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&app={app_name}&deviceId={self.join_device_id}"
                requests.get(open_app_url)

    async def control_website(self, website_url, device):
        if device == "pc":
            webbrowser.open(website_url)
        elif device == "phone":
            # Send the URL to the phone using Join API
            open_website_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&url={website_url}&deviceId={self.join_device_id}"
            requests.get(open_website_url)
        else:
            raise ValueError(f"Unknown device type: {device}")

    async def search_operate(self, search_platform, search_content, device):
        if search_platform == "google":
            try:
                # Construct the Google search URL
                search_url = f"https://www.google.com/search?q={search_content}"
                # Open the default web browser and perform the search
                if device == "pc":
                    webbrowser.open(search_url)
                elif device == "phone":
                    phone_search_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&url={search_url}&deviceId={self.join_device_id}"
                    requests.get(phone_search_url)

            except Exception as e:
                print(f"Error: {e}")
        
        elif search_platform == "youtube":
            if device == "pc":
                kit.playonyt(search_content)
                sleep(1)
                pyautogui.press("space")
            elif device == "phone":
                search_url = self.get_first_youtube_link(search_content)
                phone_search_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&url={search_url}&deviceId={self.join_device_id}"
                requests.get(phone_search_url)
        
        elif search_platform == "inside device":
            sleep(.2)
            pyautogui.click(702,1079)
            sleep(.2)
            pyautogui.click(857,1054)
            pyautogui.typewrite(search_content)
            sleep(.2)
            pyautogui.press("enter")
    
    async def simulate_type(self, typing_content, device):
        pyautogui.typewrite(typing_content)
        sleep(1)
        pyautogui.press("enter")

    async def control_system_features(self, action, device):
        def minimize_all():
            pyautogui.hotkey('win', 'm')
        def minimize_current_window():
            data = gw.getAllTitles()
            current_tab = data[3]
            app_instance = gw.getWindowsWithTitle(current_tab)[0]
            app_instance.minimize()
        def shutdown():
            # os.system("shutdown /s /t 5")
            pass
        def sleep():
            # os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            pass
        def restart():
            # os.system("shutdown /r /t 5")
            pass
        def switch_window():
            pyautogui.hotkey('alt', 'tab')
        def pause():
            pyautogui.press("playpause")
        def enter():
            pyautogui.press('enter')
        def full_screen():
            pyautogui.press('f')
        def space():
            pyautogui.press('space')
        def open_new_tab():
            time.sleep(.2)  # Small delay so you can focus the browser
            pyautogui.hotkey('ctrl', 't')
        def close_browser_tab():
            time.sleep(.2)  # Small delay so you can focus the browser
            pyautogui.hotkey('ctrl', 'w')
        def select_all():
            time.sleep(.2)
            pyautogui.hotkey('ctrl','a')
        def copy():
            time.sleep(.2)
            pyautogui.hotkey('ctrl','c')
        def paste():
            time.sleep(.2)
            pyautogui.hotkey('ctrl','v')

        actions = {
            "minimize all window": minimize_all,
            "minimize current window": minimize_current_window,
            "shutdown": shutdown,
            "sleep": sleep,
            "restart":restart,
            "switch window": switch_window,
            "pause": pause,
            "hit enter": enter,
            "full screen": full_screen,
            "hit space": space,
            "close browser tab": close_browser_tab,
            "open new tab":open_new_tab,
            "select all": select_all,
            "copy":copy,
            "paste":paste
        }

        # Execute the action if it exists
        if action in actions:
            actions[action]()
        else:
            raise ValueError(f"Unknown control type: {action}")

    async def device_information(self, information_type, device):
        async def internet_speed():
            try:
                st = speedtest.Speedtest()
                st.get_best_server()
                download = round(st.download() / 1_000_000, 2)
                upload = round(st.upload() / 1_000_000, 2)
                ping = st.results.ping
                return {
                    "download_mbps": download,
                    "upload_mbps": upload,
                    "ping_ms": ping
                }
            except Exception as e:
                print(f"Error: {e}")
                return None
        
        async def ip_address():
            local_ip = socket.gethostbyname(socket.gethostname())
            return local_ip
        
        actions = {
            "ip address": ip_address,
            "internet speed": internet_speed}
        
        if information_type in actions:
            result = await actions[information_type]()
        else:
            raise ValueError(f"Unknown control type: {information_type}")
        
        return result
    
    async def adjust_settings(self, value_type, adjustment_type, value, device):
        try:
            numeric_value = int(str(value).replace('%', '').strip())

            if value_type.lower() == "brightness":
                await self._adjust_brightness(adjustment_type, numeric_value)

            elif value_type.lower() == "volume":
                await self._adjust_volume(adjustment_type, numeric_value)

            else:
                print(f"⚠️ Unsupported value type: {value_type}")

        except Exception as e:
            print(f"❌ Error adjusting settings: {e}")

    async def _adjust_brightness(self, adjustment_type, numeric_value):
        current_brightness = sbc.get_brightness(display=0)[0]
        if adjustment_type.lower() == "increase":
            sbc.set_brightness(min(current_brightness + numeric_value, 100))
        elif adjustment_type.lower() == "decrease":
            sbc.set_brightness(max(current_brightness - numeric_value, 0))
        elif adjustment_type.lower() == "set":
            sbc.set_brightness(numeric_value)
        else:
            print(f"⚠️ Unknown brightness adjustment type: {adjustment_type}")

    async def _adjust_volume(self, adjustment_type, numeric_value):
        current_volume = round(100 * self.volume.GetMasterVolumeLevelScalar())

        if adjustment_type.lower() == "increase":
            target_volume = min(current_volume + numeric_value, 100)
        elif adjustment_type.lower() == "decrease":
            target_volume = max(current_volume - numeric_value, 0)
        elif adjustment_type.lower() == "set":
            target_volume = min(max(numeric_value, 0), 100)
        else:
            print(f"⚠️ Unknown volume adjustment type: {adjustment_type}")
            return

        self._set_volume_precisely(target_volume)

    def _set_volume_precisely(self, target_volume):
        """Adjusts volume step-by-step using hotkeys."""
        def is_odd(num):
            return num % 2 != 0

        current_volume = round(100 * self.volume.GetMasterVolumeLevelScalar())

        # Align to even numbers to avoid infinite loop
        if is_odd(current_volume):
            current_volume += 1
        if is_odd(target_volume):
            target_volume += 1

        while target_volume != current_volume:
            if target_volume > current_volume:
                pyautogui.hotkey('volumeup')
            elif target_volume < current_volume:
                pyautogui.hotkey('volumedown')
            sleep(0.15)
            current_volume = round(100 * self.volume.GetMasterVolumeLevelScalar())

    def search_app_windows(self, app_name):
        l = []
        data = gw.getAllTitles()
        for i in data:
            if app_name in i:
                l.append(i)
        return l
    
    def get_first_youtube_link(self,query):
        ydl_opts = {"quiet": True, "noplaylist": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            return f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"

    def get_best_app_match(self, query):
        query = query.lower().strip()
        if query == "cmd":
            return "Command Prompt"
        else:        
            choices = list(APP_WITH_PATH.keys())
            result = process.extractOne(query, choices, score_cutoff=50)
            if result:
                match, score, _ = result
                return match
            else:
                return None # No match found

class CommunicationAutomation:
    def __init__(self):
        with open('contacts_10digit.json', "r") as f:
            self.contact_list = json.load(f)
        self.join_device_id = "c6a07d0b1b9e470eb7181498d7eb8d49" #phone
        self.join_api_key = "8680fb0ccc1249908d265c378ea0e167" 

    async def Call(self, person_name, call_media, call_type, device):
        try:
            if call_media.lower() == "sim":
                await self.SimCall(person_name)
            elif call_media.lower() == "whatsapp":
                await self.WhatsappCall(person_name,call_type,device)

        except Exception as e:
            print(f"❌ Error during calling: {e}")
    
    async def Message(self, person_name, message_media, message_content, device):
        try:
            number, actual_name = await self.get_number(person_name.lower())
            number_with_country_code = f"91{number}"

            if device == "pc":
                pass

            elif device == "phone":
                if message_media == "sim":
                    data = f"sim msg||{number_with_country_code}||{message_content}"
                    msg_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&text={data}&deviceId={self.join_device_id}"
                    requests.get(msg_url)
                    # print(f"Message sent to {actual_name} ({number})")

                elif message_media == "whatsapp":
                    data = f"whatsapp msg||{number_with_country_code}||{message_content}"
                    msg_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&text={data}&deviceId={self.join_device_id}"
                    requests.get(msg_url)
                    # print(f"Message sent to {actual_name} ({number})")

        except Exception as e:
            print(f"❌ Error sending message: {e}")

    async def SimCall(self, person_name):
        number, actual_name = await self.get_number(person_name.lower())
        call_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&callnumber={number}&deviceId={self.join_device_id}"
        requests.get(call_url)
        # print(f"calling {actual_name} : {number}")

    async def WhatsappCall(self, person_name, call_type, device):
        number, actual_name = await self.get_number(person_name.lower())
        number_with_country_code = f"91{number}"

        if call_type.lower() == "voice":
            data = f"whatsapp voice call||{number_with_country_code}"
            call_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&text={data}&deviceId={self.join_device_id}"
            requests.get(call_url)

        elif call_type.lower() == "video":
            data = f"whatsapp video call||{number_with_country_code}"
            call_url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={self.join_api_key}&text={data}&deviceId={self.join_device_id}"
            requests.get(call_url)

    async def get_number(self, name):
        choices = list(self.contact_list.keys())
        result = process.extractOne(name, choices, score_cutoff=50)
        if result:
            match, score, _ = result
            number = self.contact_list[match]
            return number, match
        else:
            return None # No match found

class HomeController:
    def __init__(self, mqtt_server="broker.mqtt.cool"):
        self.client = paho.Client(paho.CallbackAPIVersion.VERSION2)
        self.mqtt_server = mqtt_server

        self.topic_map = {
            "bedroom": "somn194_control/bedroom_appliance",
            "outside": "somn194_control/outside_appliance",
            "work": "somn194_control/work_appliance"
        }

        self.device_relay_map = {
            "bedroom light":     ("bedroom", "relay1"),
            "bedroom fan":       ("bedroom", "relay4"),
            "bedroom bulb":      ("bedroom", "relay3"),
            "side led":          ("bedroom", "relay2"),

            "bathroom light":    ("outside", "relay3"),
            "stair light":        ("outside", "relay1"),
            "outdoor light":     ("outside", "relay2"),
            "outdoor camera":    ("outside", "relay4"),

            "home theater":      ("work", "relay1"),
            "pc":                ("work", "relay2"),
            "soldering iron":    ("work", "relay3"),
            "main led":          ("work", "relay4"),
            "raspberry pi":      ("work", "relay5")
        }

        self.blocked_off = {"pc", "raspberry pi"}

    async def mqtt_publish(self, command, topic):
        await asyncio.to_thread(self._publish_sync, command, topic)

    def _publish_sync(self, command, topic):
        try:
            result = self.client.connect(self.mqtt_server, 1883, 60)
            if result == 0:
                self.client.publish(topic, command, 0)
                time.sleep(1)
        except Exception as e:
            print(f"❌ MQTT error: {e}")

    async def control_device(self, controlled_device, controlled_state):
        if controlled_device not in self.device_relay_map:
            print(f"Unknown device: {controlled_device}")
            return

        topic_key, relay_id = self.device_relay_map[controlled_device]
        topic = self.topic_map[topic_key]

        # Handle special case: restricted OFF permission
        if controlled_state == "off" and controlled_device in self.blocked_off:
            print(f"I don't have permission to turn off {controlled_device.title()}!")
            return

        command = f"{relay_id}_{controlled_state}"
        await self.mqtt_publish(command, topic)
        print(f"Turned {controlled_state} {controlled_device}")

class LEDStripController:
    async def set_led_segment(self, segment_name, rgb_colour_code, brightness_value=255):
        segment_id = SEGMENT_MAP.get(segment_name.lower())
        if isinstance(rgb_colour_code, str):
            try:
                rgb_colour_code = ast.literal_eval(rgb_colour_code)
            except Exception as e:
                print("❌ Invalid string format for RGB. Expected a list like '[255, 0, 0]'.")
                rgb_colour_code = [0,0,0]
        if segment_id is None:
            print(f"❌ Unknown segment: {segment_name}")
            return

        payload = {
            "on": True,
            "bri": 210,
            "ps": -1,
            "seg": []
        }

        if segment_id == 8:  # 'all'
            for name, sid in SEGMENT_MAP.items():
                if sid == 8 or sid == 9:
                    continue  # skip the 'all' alias
                payload["seg"].append({
                    "id": sid,
                    "col": [rgb_colour_code, [0, 0, 0], [0, 0, 0]],
                    "bri": brightness_value
                })
            await self.send_wled_request(payload,WLED_IP)
            payload2 = {
            "on": True,
            "bri": brightness_value,
            "seg": [{
                "id": 0,
                "col": [rgb_colour_code, [0, 0, 0], [0, 0, 0]],
            }]}
            print("🎨 Applying color to ALL segments.")
            await self.send_wled_request(payload2,BACK_WLED_IP)

        elif segment_id == 9:
            payload = {
            "on": True,
            "bri": brightness_value,
            "seg": [{
                "id": 0,
                "col": [rgb_colour_code, [0, 0, 0], [0, 0, 0]],
            }]}
            print(f"🎯 Applying color to segment: {segment_name} (ID: {segment_id})")
            await self.send_wled_request(payload,BACK_WLED_IP)

        else:
            payload["seg"].append({
                "id": segment_id,
                "col": [rgb_colour_code, [0, 0, 0], [0, 0, 0]],
                "bri": brightness_value
            })
            print(f"🎯 Applying color to segment: {segment_name} (ID: {segment_id})")
            await self.send_wled_request(payload,WLED_IP)
            
    async def set_segment_mode(self, strip_mode):
        payload = None

        if strip_mode == "musicSync":
            payload = {
                "on": True,
                "bri": 200,
                "ps": -1,
                "seg": [{
                    "id": 0,
                    "on": True,
                    "bri": 255,
                    "col": [[255, 255, 255], [0, 0, 0], [0, 0, 0]],
                    "fx": 165,
                    "sx": 101,
                    "ix": 148,
                    "pal": 72
                }]
            }
        elif strip_mode == "workMode":
            payload = {
                "on": True,
                "bri": 200,
                "ps": 3
            }
        elif strip_mode == "shootingMode":
            payload = {
                "on": True,
                "bri": 200,
                "ps": 5
            }
        else:
            print(f"⚠️ Unknown strip mode '{strip_mode}'. Falling back to 'workMode'.")
            payload = {
                "on": True,
                "bri": 200,
                "ps": 1
            }
        if payload:
            await self.send_wled_request(payload, WLED_IP)

    async def send_wled_request(self, payload, IP):
        url = f"http://{IP}/json/state"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        print("✅ WLED command sent successfully.")
                    else:
                        print(f"❌ Failed with code {resp.status}")
        except Exception as e:
            print(f"❌ Exception in WLED request: {e}")

class ComputerVisionActivation:
    def __init__(self):
        pass   

class CommandExecutor:
    def __init__(self):
        self.home_controller = HomeController()
        self.led_controller = LEDStripController()
        self.windows_automation = WindowsAutomation()
        self.communication_automation = CommunicationAutomation()

        self.function_map = {
            "HomeControl": self.execute_home_control,
            "SetLedStripSegment": self.execute_set_led_strip,
            "SetLedStripMode": self.execute_led_strip_mode,
            "AppControl": self.execute_app_control,
            "OpenWebsite": self.execute_website_control,
            "PerformSearch": self.execute_search_operation,
            "SimulateTyping": self.execute_simulate_typing,
            "SystemControl":self.execute_system_control,
            "GetDeviceInfo": self.execute_device_info,
            "AdjustSetting": self.execute_adjust_setting,
            "Call":self.execute_call,
            "Message": self.execute_message
            
        }

    async def execute(self, actions: list):
        results = []
        for action_obj in actions:
            function_name = action_obj.get("functionName")
            arguments = action_obj.get("arguments", {})

            handler = self.function_map.get(function_name)
            if handler:
                try:
                    if inspect.iscoroutinefunction(handler):
                        result = await handler(arguments)
                    else:
                        result = handler(arguments)

                    if result is not None:
                        results.append({
                            "function_name":function_name,
                            "result":result
                        })

                except Exception as e:
                    print(f"❌ Error executing '{function_name}': {e}")
            else:
                print(f"⚠️ No handler found for function: {function_name}")
        return results
    
    async def execute_home_control(self, args: dict):
        formatted_args = {
            "controlled_device": args["controlledAppliances"],
            "controlled_state": args["controlledState"]
        }
        await self.home_controller.control_device(**formatted_args)

    async def execute_set_led_strip(self, args: dict):
        formatted_args = {
            "segment_name": args["segmentName"],
            "rgb_colour_code": args["rgbColourCode"],
            "brightness_value": args["brightnessValue"]
        }
        await self.led_controller.set_led_segment(**formatted_args)

    async def execute_led_strip_mode(self, args: dict):
        formatted_args = {
            "strip_mode": args["stripMode"]
        }
        await self.led_controller.set_segment_mode(**formatted_args)
    
    async def execute_app_control(self, args: dict):
        formatted_args = {
            "app_name": args["applicationName"],
            "control_type" : args["applicationControlType"],
            "device": args["device"]
        }
        await self.windows_automation.control_application(**formatted_args)
    
    async def execute_website_control(self, args: dict):
        formatted_args = {
            "website_url": args["websiteUrl"],
            "device": args["device"]
        }
        await self.windows_automation.control_website(**formatted_args)
    
    async def execute_search_operation(self, args: dict):
        formatted_args = {
            "search_platform": args["searchPlatform"],
            "search_content": args["searchContent"],
            "device": args["device"]
        }
        await self.windows_automation.search_operate(**formatted_args)
    
    async def execute_simulate_typing(self, args: dict):
        formatted_args = {
            "typing_content": args["typingContent"],
            "device": args["device"]
        }
        await self.windows_automation.simulate_type(**formatted_args)

    async def execute_system_control(self, args: dict):
        formatted_args = {
            "action": args["action"],
            "device": args["device"]
        }
        await self.windows_automation.control_system_features(**formatted_args)
    
    async def execute_device_info(self, args: dict):
        formatted_args = {
            "value_type": args["informationType"],
            "device": args["device"]
        }
        result = await self.windows_automation.device_information(**formatted_args)
        return result
    
    async def execute_adjust_setting(self, args:dict):
        formatted_args = {
            "value_type": args["valueType"],
            "adjustment_type": args["adjustmentType"],
            "value": args["value"],
            "device": args["device"]
        }
        await self.windows_automation.adjust_settings(**formatted_args)

    async def execute_call(self, args:dict):
        formatted_args = {
            "person_name": args["personName"],
            "call_media": args["callMedia"],
            "call_type": args["callType"],
            "device": args["device"]
        }
        await self.communication_automation.Call(**formatted_args)

    async def execute_message(self, args:dict):
        formatted_args = {
            "person_name": args["personName"],
            "message_media": args["messageMedia"],
            "message_content": args["messageContent"],
            "device": args["device"]
        }
        await self.communication_automation.Message(**formatted_args)

if __name__ == "__main__":
    wa = WindowsAutomation()
    ca = CommunicationAutomation()
    hm = HomeController()
    lc = LEDStripController()
    print(asyncio.run(ca.Call("ma","sim","voice","phone")))