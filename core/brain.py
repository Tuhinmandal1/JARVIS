from dotenv import load_dotenv
import os

from google import genai
from google.genai import types

from tools.computer import open_application, APPLICATIONS

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Make sure it's set in your .env file."
    )

client = genai.Client(api_key="Your API key here")  # Replace with your actual API key

MODEL_NAME = "gemini-3.6-flash"

SYSTEM_INSTRUCTION = (
    "You are JARVIS, a helpful personal AI assistant. "
    "You are concise, a little witty, and speak like a capable assistant, "
    "not a search engine. When the user asks you to open an application, "
    "use the open_application tool rather than just describing what you'd do."
)

# --- Tool declaration: tells Gemini this function exists and how to call it ---
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

jarvis_tool = types.Tool(function_declarations=[open_application_declaration])

# Maps tool names Gemini can call -> actual Python functions that execute them
AVAILABLE_FUNCTIONS = {
    "open_application": open_application,
}


class JarvisBrain:
    def __init__(self):
        # Keeps conversation history so JARVIS has memory within a session
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
        # Record the model's function-call turn in history
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

        # Send the tool's result back to Gemini so it can phrase a natural reply
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