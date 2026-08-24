from core.brain import JarvisBrain


jarvis = JarvisBrain()

print("JARVIS AI TEST")
print("----------------")

while True:

    command = input("YOU: ")

    if command.lower() in ["exit", "quit", "shutdown"]:
        print("JARVIS: Shutting down.")
        break

    response = jarvis.ask(command)

    print("JARVIS:", response)