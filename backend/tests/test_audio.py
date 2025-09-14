import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')

if not API_TOKEN:
    raise ValueError("CLOUDFLARE_API_TOKEN environment variable is required")
if not ACCOUNT_ID:
    raise ValueError("CLOUDFLARE_ACCOUNT_ID environment variable is required")

URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/deepgram/aura-1"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# options for people
# "asteria",
# "arcas",
# "orion",
# "orpheus",
# "athena",
# "luna",
# "zeus",
# "perseus",
# "helios",
# "hera",
# "stella"

payload = {
  "text": "Hello world! This is a test of the text to speech API. I will now tell you about how great of a person you are",
  "speaker": "luna",
  "encoding": "linear16",
  "container": "wav"
}


response = requests.post(URL, headers=headers, json=payload)

# Save to mp3 file
filename = "speech.mp3"
with open(filename, "wb") as f:
    f.write(response.content)

print(f"Saved audio as {filename}")

# Play depending on OS
if os.name == "nt":  # Windows
    os.startfile(filename)
elif os.uname().sysname == "Darwin":  # macOS
    os.system(f"open {filename}")
else:  # Linux
    os.system(f"xdg-open {filename}")
