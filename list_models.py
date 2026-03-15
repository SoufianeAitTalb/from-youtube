
import google.generativeai as genai
import os

GENAI_API_KEY = "AIzaSyBa5XEk8enhhzI-QCJptFOigttDyYwmMFU"
genai.configure(api_key=GENAI_API_KEY)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error: {e}")
