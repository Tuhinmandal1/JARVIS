from dotenv import load_dotenv
import os

from google import genai
from google.genai import types

from tools.computer import open_application, APPLICATIONS
from tools.web_search import web_search
from tools.reminders import (
    add_reminder,
    list_reminders,
    delete_reminder,
    start_reminder_checker,
)
from tools.file_search import file_search

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Make sure it's set in your .env file."
    )

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.6-flash"

SYSTEM_INSTRUCTION = (
    "You are JARVIS, a helpful personal AI assistant. "
    "You are concise, a little witty, and speak like a capable assistant, "
    "not a search engine. Use the tools available to you rather than just "
    "describing what you'd do. For reminders, always convert relative times "
    "like 'in 10 minutes' or 'tomorrow morning' into HH:MM or "
    "YYYY-MM-DD HH:MM before calling add_reminder."
)

# --- Tool declarations ---

open_application_declaration = types.FunctionDeclaration(
    name="open_application",
    description=(
        "Opens a Windows application by name. Only use application names "
        f"from this known list: {', '.join(APPLICATIONS.keys())}."
    ),
    parameters={
        "type": "object",
        "properties": {
            "application": {
                "type": "string",
                "description": "Name of the application to open, e.g. 'notepad'.",
            }
        },
        "required": ["application"],
    },
)

web_search_declaration = types.FunctionDeclaration(
    name="web_search",
    description="Searches the web and returns a summary of top results. Use this for anything requiring current or factual information you're not certain about.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            }
        },
        "required": ["query"],
    },
)

add_reminder_declaration = types.FunctionDeclaration(
    name="add_reminder",
    description="Adds a reminder that will be spoken aloud when it comes due.",
    parameters={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "What to remind the user about.",
            },
            "time_str": {
                "type": "string",
                "description": "When to remind, formatted as HH:MM (today) or YYYY-MM-DD HH:MM.",
            },
        },
        "required": ["text", "time_str"],
    },
)

list_reminders_declaration = types.FunctionDeclaration(
    name="list_reminders",
    description="Lists all upcoming reminders that haven't triggered yet.",
    parameters={"type": "object", "properties": {}},
)

delete_reminder_declaration = types.FunctionDeclaration(
    name="delete_reminder",
    description="Deletes a reminder by its id (shown by list_reminders).",
    parameters={
        "type": "object",
        "properties": {
            "reminder_id": {
                "type": "string",
                "description": "The short id of the reminder to delete.",
            }
        },
        "required": ["reminder_id"],
    },
)

file_search_declaration = types.FunctionDeclaration(
    name="file_search",
    description="Searches for files by name within the user's home folder (Desktop, Documents, Downloads, Pictures, etc).",
    parameters={
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Full or partial filename to search for.",
            }
        },
        "required": ["filename"],
    },
)

jarvis_tool = types.Tool(
    function_declarations=[
        open_application_declaration,
        web_search_declaration,
        add_reminder_declaration,
        list_reminders_declaration,
        delete_reminder_declaration,
        file_search_declaration,
    ]
)

AVAILABLE_FUNCTIONS = {
    "open_application": open_application,
    "web_search": web_search,
    "add_reminder": add_reminder,
    "list_reminders": list_reminders,
    "delete_reminder": delete_reminder,
    "file_search": file_search,
}

# Start the background thread that watches for due reminders and speaks them
start_reminder_checker()


class JarvisBrain:
    def __init__(self):
        self.history = []

    def ask(self, user_input: str) -> str:
        self.history.append(
            types.Content(role="user", parts=[types.Part(text=user_input)])
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=self.history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[jarvis_tool],
            ),
        )

        candidate = response.candidates[0]
        function_call = self._extract_function_call(candidate)

        if function_call:
            return self._handle_function_call(candidate, function_call)

        final_text = response.text or "I'm not sure how to respond to that."
        self.history.append(
            types.Content(role="model", parts=[types.Part(text=final_text)])
        )
        return final_text

    def _extract_function_call(self, candidate):
        for part in candidate.content.parts:
            if part.function_call:
                return part.function_call
        return None

    def _handle_function_call(self, candidate, function_call) -> str:
        self.history.append(candidate.content)

        name = function_call.name
        args = dict(function_call.args) if function_call.args else {}

        func = AVAILABLE_FUNCTIONS.get(name)

        if func is None:
            result_text = f"Unknown tool requested: {name}"
        else:
            try:
                result_text = func(**args)
            except Exception as error:
                result_text = f"Error running {name}: {error}"

        function_response_part = types.Part.from_function_response(
            name=name,
            response={"result": result_text},
        )
        self.history.append(
            types.Content(role="user", parts=[function_response_part])
        )

        follow_up = client.models.generate_content(
            model=MODEL_NAME,
            contents=self.history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[jarvis_tool],
            ),
        )

        final_text = follow_up.text or result_text
        self.history.append(
            types.Content(role="model", parts=[types.Part(text=final_text)])
        )
        return final_text
