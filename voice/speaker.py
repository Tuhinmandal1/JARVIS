import pyttsx3


class Speaker:
    def __init__(self):
        self.engine = pyttsx3.init()

        self.engine.setProperty("rate", 175)
        self.engine.setProperty("volume", 1.0)

    def speak(self, text):
        print(f"JARVIS: {text}")

        self.engine.say(text)
        self.engine.runAndWait()


if __name__ == "__main__":
    speaker = Speaker()
    speaker.speak("Systems online. I am Jarvis.")