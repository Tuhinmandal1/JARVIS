import subprocess


APPLICATIONS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
}


def open_application(application: str) -> str:
    """
    Open a Windows application.

    Args:
        application: Name of the application.

    Returns:
        Result of the operation.
    """

    application = application.lower().strip()

    if application not in APPLICATIONS:
        available = ", ".join(APPLICATIONS.keys())
        return f"I don't know that application yet. Available: {available}"

    try:
        subprocess.Popen(APPLICATIONS[application])

        return f"Opened {application} successfully."

    except Exception as error:
        return f"Unable to open {application}: {error}"