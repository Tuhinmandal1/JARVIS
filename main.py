from voice.listener import Listener
from voice.speaker import Speaker


def main():
    listener = Listener()
    speaker = Speaker()

    speaker.speak("Systems online. How may I assist you?")

    while True:
        command = listener.listen()

        if not command:
            continue

        command = command.lower()

        if "shutdown jarvis" in command:
            speaker.speak("Shutting down. Goodbye.")
            break

        if "hello" in command or "hi" in command:
            speaker.speak("Hello. I am Jarvis.")

        elif "who are you" in command:
            speaker.speak(
                "I am Jarvis, your personal artificial intelligence assistant."
            )

        elif "how are you" in command:
            speaker.speak(
                "All systems are operational."
            )

        else:
            speaker.speak(
                f"You said {command}."
            )


if __name__ == "__main__":
    main()