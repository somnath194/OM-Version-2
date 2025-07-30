import pyttsx3

Assistant = pyttsx3.init('sapi5')
voices = Assistant.getProperty('voices')
#print(voices)
Assistant.setProperty('voice' , voices[1].id)
Assistant.setProperty('rate', 190)

def speak(audio):
    print("   ")
    audio1 = "hi how are you helo " + str(audio)
    Assistant.say(audio)
    print(f": {audio}")
    Assistant.runAndWait()
