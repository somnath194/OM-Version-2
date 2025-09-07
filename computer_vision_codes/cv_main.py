import cv2
import time
import base64
import numpy as np
import mediapipe as mp
import autopy
import face_recognition
from openai import OpenAI
import os
import pickle
import numpy as np
from dotenv import load_dotenv
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import absl.logging
absl.logging.set_verbosity('error')
from computer_vision_codes import hand_tracking_module as htm
import urllib.request
import threading


class ComputerVisionActivation:
    def __init__(self):
        file = open('D:\\Programs\\OM-Version-2\\computer_vision_codes\\EncodeFile.p', 'rb')
        encodeListKnownWithNames = pickle.load(file)
        file.close()
        self.encodeListKnown, self.imgNames = encodeListKnownWithNames

        self.cap = None
        self.running = False
        self.detector = mp.solutions.hands.Hands(max_num_hands=1)
        self.client = None

        # Load OpenAI
        load_dotenv(dotenv_path="D:\\Programs\\OM-Version-2\\.env", override=True)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)

        self.model = "gpt-4o-mini"

        # Configurations
        self.wCam, self.hCam = 640, 480
        self.wScr, self.hScr = autopy.screen.size()
        self.frameRx, self.frameRy = 100, 50
        self.alpha = 0.25  # smoothing factor for exponential moving average
        self.clickCooldown = 0.3
        self.clickThreshold = 35
        self.detector = htm.handDetector(maxHands=1)

        # Hand mouse variables
        self.plocx, self.plocy = 0, 0
        self.clocx, self.clocy = 0, 0
        self.lastClickTime = 0
        self.pTime = 0
   
    def computer_vision_mode(self,camera_selection , mode="raw", state = "activate"):
        """Main feed loop. Mode decides what processing is applied."""
        data = None
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("[ERROR] Webcam not accessible.")
            return

        self.running = True

        if state == "deactivate":
            self.stop_feed()
            return
        else:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    continue

                if mode == "face recognition":
                    frame, data = self._face_recognition_mode(frame)

                elif mode == "hand mouse":
                    frame = self._hand_mouse_mode(frame)

                cv2.imshow("Computer Vision Feed", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_feed()
                    break

            self.cap.release()
            cv2.destroyAllWindows()

    def vision_quary_mode(self, camera_selection, mode, query):
        """Process a single image with vision query, ocr, etc."""
        show_time = 5  # seconds to show the image if not using openai query

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("[ERROR] Webcam not accessible.")
            return

        # warm up camera - read a few frames first
        for _ in range(5):
            ret, frame = self.cap.read()
            if not ret:
                continue
        self.cap.release()

        if mode == "image_query":
            data = self._image_query(frame, query)
            response_text = f"Vision Response: {data}"

        elif mode == "ocr":
            data = self._OCR_mode(frame)
            response_text = f"Extracted Text: {data}"
        
        elif mode == "face_recognition":
            frame, name = self._face_recognition_mode(frame)
            response_text = f"Identified person: {name}" if name else "No known person identified."

        cv2.imshow("Captured Frame", frame)
        cv2.waitKey(show_time * 1000)  # time in ms
        cv2.destroyAllWindows()

        return response_text

    def stop_feed(self):
        self.running = False

    # ---------------- Face Recognition ----------------
    def _face_recognition_mode(self, frame):
        name = None
        imgS = cv2.resize(frame, (0,0), None, 0.2, 0.2)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS, model='hog')
        encodeCurframe = face_recognition.face_encodings(imgS, faceCurFrame)
        
        for faceEncode, faceLoc in zip(encodeCurframe, faceCurFrame):
            matches = face_recognition.compare_faces(self.encodeListKnown, faceEncode)
            faceDis = face_recognition.face_distance(self.encodeListKnown, faceEncode)
            
            matchIndex = np.argmin(faceDis)
            if matches[matchIndex]:
                name = self.imgNames[matchIndex]

                top, right, bottom, left = faceLoc
                top, right, bottom, left = top*5, right*5, bottom*5, left*5
                cv2.rectangle(frame, (left, top), (right, bottom), (0,0,255), 2)

                # cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0,0,255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left+6, bottom+25), font, 1.0, (255,255,255), 1)

        return frame, name

    # ---------------- Hand Mouse Mode ----------------
    def _hand_mouse_mode(self, frame):
        img = cv2.resize(frame, (self.wCam, self.hCam))
        img = self.detector.findHands(img)
        lmList, bbox = self.detector.findPosition(img)

        if len(lmList) != 0:
            x1, y1 = lmList[8][1:]  # Index finger tip
            x2, y2 = lmList[12][1:]  # Middle finger tip

            fingers = self.detector.fingersUp()
            cv2.rectangle(img, (self.frameRx, self.frameRy), (self.wCam - self.frameRx, self.hCam - self.frameRx - self.frameRy), (255, 0, 255), 2)

            # Moving Mode
            if fingers[1] == 1 and fingers[2] == 0:
                x3 = np.interp(x1, (self.frameRx, self.wCam - self.frameRx), (0, self.wScr))
                y3 = np.interp(y1, (self.frameRy, self.hCam - self.frameRx - self.frameRy), (0, self.hScr))

                self.clocx = (1 - self.alpha) * self.plocx + self.alpha * x3
                self.clocy = (1 - self.alpha) * self.plocy + self.alpha * y3

                self.clocx = max(0, min(self.clocx, self.wScr - 1))
                self.clocy = max(0, min(self.clocy, self.hScr - 1))

                autopy.mouse.move(self.wScr - self.clocx, self.clocy)
                cv2.circle(img, (x1, y1), 5, (255, 0, 255), cv2.FILLED)
                self.plocx, self.plocy = self.clocx, self.clocy

            # Clicking Mode
            if fingers[1] == 1 and fingers[2] == 1:
                length, img, lineInfo = self.detector.findDistance(8, 12, img, draw=False)
                if length < self.clickThreshold and (time.time() - self.lastClickTime) > self.clickCooldown:
                    self.lastClickTime = time.time()
                    autopy.mouse.click()
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 10, (0, 255, 0), cv2.FILLED)

        # FPS Calculation
        cTime = time.time()
        fps = 1 / (cTime - self.pTime) if cTime != self.pTime else 0
        self.pTime = cTime
        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 0), 3)

        return img
    
    # ---------------- OpenAI Vision ----------------
    def _image_query(self, frame, query):
        """
        Takes an OpenCV frame + text query,
        sends to OpenAI Vision model,
        and returns the response as string.
        """
        # Convert frame to JPEG bytes → base64
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode("utf-8")

        # Send to OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ],
        )

        return response.choices[0].message.content

    def _OCR_mode(self, frame):
        """
        Takes an OpenCV frame,
        sends to OpenAI Vision model,
        and returns the response of extractid text as string.
        """
        query = "You are an OCR expert so extract all text and special characters from this image."
        # Convert frame to JPEG bytes → base64
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode("utf-8")

        # Send to OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ],
        )

        return response.choices[0].message.content

    def _show_frame_async(self, frame, show_time):
        """Show frame in separate thread without blocking return."""
        def _show():
            start = time.time()
            while True:
                cv2.imshow("Captured Frame", frame)
                # keep updating window until timeout
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                if time.time() - start > show_time:
                    break
            cv2.destroyAllWindows()
        threading.Thread(target=_show, daemon=True).start()



# ---------------- Example Usage ----------------
if __name__ == "__main__":
    cv = ComputerVisionActivation()
    data = cv.computer_vision_mode(camera_selection=None, mode="face recognition", state="activate")  # change to "handmouse" or "openai"
    print("The data is:", data)
