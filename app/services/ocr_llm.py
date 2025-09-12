from google import genai
from google.genai import types
import pathlib
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def extract_text_llm(file_path: str) -> tuple[str, int]:
    """
    Extract text from a PDF or image using Gemini model instead of Tesseract OCR.
    Returns: (extracted_text, num_pages)
    """
    filepath = pathlib.Path(file_path)

    # Prompt for extraction
    prompt = "Extract all visible text from this document as plain text."

    # Send the file + prompt to Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",   
        contents=[
            types.Part.from_bytes(
                data=filepath.read_bytes(),
                mime_type="application/pdf" if file_path.lower().endswith(".pdf") else "image/png",
            ),
            prompt
        ]
    )

    # Extract plain text
    extracted_text = response.text.strip() if response.text else ""

    # Page count (Gemini doesn’t give pages directly → fallback to 1)
    # If you still want page count, you can combine pdf2image just for counting
    num_pages = 1  

    return extracted_text, num_pages
