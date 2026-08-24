import speech_recognition as sr


class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def listen(self):
        with self.microphone as source:
            print("JARVIS: Listening...")

            self.recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio)

            print(f"YOU: {text}")

            return text

        except sr.UnknownValueError:
            print("JARVIS: I didn't understand that.")

            return ""

        except sr.RequestError as error:
            print(f"JARVIS: Speech recognition error: {error}")

            return ""


if __name__ == "__main__":
    listener = Listener()

    while True:
        text = listener.listen()

        if text:
            print(f"Recognized: {text}")