import requests

url = "http://localhost:5000/api/ask/voice"
# Updated to match your actual file name!
audio_file_path = "../untitled2.ogg" 

print(f"Loading {audio_file_path}...")
with open(audio_file_path, "rb") as f:
    audio_data = f.read()

print("Sending audio to local Flask server...")
response = requests.post(url, data=audio_data)

print("\n--- Server Response ---")
print(f"Status Code: {response.status_code}")
try:
    print(f"JSON Response: {response.json()}")
except Exception:
    print(f"Raw Response: {response.text}")