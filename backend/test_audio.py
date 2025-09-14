import requests
import os

API_TOKEN = "K2PbiovkXjD9At52zuwVqOsIw1jcU1W1tDZL3OcT"
ACCOUNT_ID = "55072dd902d152710c0916f760f79a05"
URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/deepgram/aura-1"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

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
