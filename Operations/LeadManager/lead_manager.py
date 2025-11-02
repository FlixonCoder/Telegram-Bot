from google import genai
from google.genai import types
import os
import requests
from bs4 import BeautifulSoup
import time
from Data.SystemInstructions import system_instructions
from datetime import datetime
from dotenv import load_dotenv
import re, json
from ..Storage.storage_manager import insert_many, get_by_link, get_all

load_dotenv()

global output
# -----------------------------------------
# CONFIG
# -----------------------------------------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found. Please set it as an environment variable.")

client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"



# -----------------------------------------
# READ AND WRITE FILES
# -----------------------------------------
file_path = f"Data/final.json"
def append_to_json(file_path, new_data):
    # If file doesn't exist, create an empty list
    if not os.path.exists(file_path):
        data = []
    else:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

    # Normalize new_data to a list
    if not isinstance(new_data, list):
        new_data = [new_data]

    # Create a set of existing links
    existing_links = {entry.get("link") for entry in data}

    # Filter out duplicates
    unique_entries = [entry for entry in new_data if entry.get("link") not in existing_links]

    if not unique_entries:
        print("⚠️ No new entries added — link(s) already exist.")
        return

    # Append only unique entries
    data.extend(unique_entries)

    # Write back to file
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    response = f"✅ {len(unique_entries)} new item(s) added successfully!"
    return response

# -----------------------------------------
# CLEANING JSON
# -----------------------------------------
def clean_json_string(text):
    """Cleans markdown and invisible characters from model output."""
    if not text or not text.strip():
        return ""
    # Remove ```json and ``` markers
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
    # Remove ANSI escape codes (color codes)
    cleaned = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", cleaned)
    # Remove non-breaking spaces and extra whitespace
    cleaned = cleaned.replace("\u200b", "").strip()
    return cleaned


# -----------------------------------------
# LINK VALIDATION
# -----------------------------------------
def verify_link(link: str):
    if not link.startswith("http"):
        link = "https://" + link
    try:
        res = requests.get(link, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.title.string.strip() if soup.title else ""
            return True, title
        return False, None
    except Exception:
        return False, None

# -----------------------------------------
# GEMINI CALL (with retries)
# -----------------------------------------
def generate_with_retry(prompt, max_retries=3, delay=3):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instructions
                ),
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                print(f"⚠️ Gemini overloaded (503). Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise e

# -----------------------------------------
# PROCESS INPUT
# -----------------------------------------
def process_input(input_text: str):
    print("\n🔍 Verifying provided links...\n")
    for line in input_text.splitlines():
        if line.lower().startswith("link:"):
            link = line.split(":", 1)[1].strip()
            valid, title = verify_link(link)
            print(f"→ {link}  :  {'✅ Valid' if valid else '❌ Invalid'}")

    print("\n🧠 Generating structured data...\n")

    full_prompt = f"Input:\n{input_text.strip()}\n\nPlease organize this data according to the given system instructions."

    output = generate_with_retry(full_prompt)
    return output

# -----------------------------------------
# MAIN
# -----------------------------------------
def lead_manager(input_text: str):
    """
    Processes input text using Gemini, parses JSON response,
    checks for existing links in MongoDB, and inserts only new ones.
    """
    print("🔹 Lead Manager Activated (MongoDB Mode)\n")

    # Step 1 — Get model response
    final_output = process_input(input_text)

    # Step 2 — Clean and parse model output to JSON
    cleaned = re.sub(r"^```(?:json)?|```$", "", final_output.strip(), flags=re.I).strip()

    try:
        payload = json.loads(cleaned)
    except Exception as e:
        print(f"❌ JSON decode failed: {e}")
        print("Raw cleaned string:", repr(cleaned))
        return None

    # Normalize payload into a list
    if not isinstance(payload, list):
        payload = [payload]

    print(f"🧩 Parsed {len(payload)} item(s) from Gemini.\n")

    # Step 3 — Validate each entry before insertion
    unique_to_insert = []

    for entry in payload:
        link = entry.get("link")
        if not link:
            print(f"⚠️ Skipping entry (no link field): {entry}")
            continue

        # --- Verify link and set status ---
        valid, title = verify_link(link)
        entry["status"] = "verified" if valid else "invalid"

        # --- Add timestamp ---
        entry["timestamp"] = datetime.now().isoformat()  # e.g. "2025-10-25T17:20:43.512Z"

        # --- Auto-fill missing title ---
        if valid and title and not entry.get("title"):
            entry["title"] = title

        # --- Check for duplicates ---
        existing_doc = get_by_link(link)
        if existing_doc:
            print(f"⚠️ Skipping duplicate (already in DB): {link}")
        else:
            unique_to_insert.append(entry)


    # Step 4 — Push unique entries to MongoDB
    if unique_to_insert:
        insert_many(unique_to_insert)
        response = f"✅ Successfully inserted {len(unique_to_insert)} new document(s) into MongoDB."
    else:
        response = "⚠️ No new unique entries to insert — all links already exist."

    print("\n✅ Lead Manager process complete.")
    return response
