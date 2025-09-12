import os
from dotenv import load_dotenv
from google.generativeai import configure

# Load .env file
load_dotenv()

# Gemini API
configure(api_key=os.getenv("GEMINI_API_KEY"))

# Tesseract path
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "C:\\Users\\HP\\Desktop\\Argus_Backend\\Uploads")
POPPLER_PATH = r"C:\path\to\poppler\bin"

 