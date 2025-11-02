from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found. Please set it as an environment variable.")

brain_instructions = ""

client = genai.Client()
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=brain_instructions
    )
)

def brain(prompt: str):
    response = chat.send_message(prompt)
    return response.text

while True:
    x = input("Enter: ")
    print(brain(x))