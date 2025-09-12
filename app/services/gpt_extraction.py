from google import genai
from google.genai import types
import pathlib
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

async def extract_with_gemini(prompt: str, file_path: str = None) -> str:
    """
    Extract structured JSON or text from a document using Gemini.
    
    Args:
        prompt (str): Instruction/schema prompt
        file_path (str, optional): Path to a PDF/image file to include in the request
    
    Returns:
        str: Raw Gemini response text
    """
    contents = [prompt]

    if file_path:
        filepath = pathlib.Path(file_path)
        mime = "application/pdf" if file_path.lower().endswith(".pdf") else "image/png"

        contents.insert(0, types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type=mime
        ))

    # Run in thread to avoid blocking FastAPI event loop
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=contents,
    )

    return response.text.strip() if response.text else ""
