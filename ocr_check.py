import os
import pathlib
import re
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer, util

# -------------------- CONFIG --------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Tesseract path
from app.core.config import TESSERACT_PATH
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

POPPLER_PATH = r"C:\Program Files\Poppler\poppler-24.08.0\Library\bin"

# Load embedding model (cached so it loads once)
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_model()
# ------------------------------------------------


# ------------ OCR FUNCTIONS ---------------------
def extract_text_tesseract(file_path: str) -> tuple[str, int]:
    file_ext = file_path.split('.')[-1].lower()
    if file_ext == "pdf":
        images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
        return text, len(images)
    else:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img), 1


def extract_text_gemini(file_path: str) -> tuple[str, int]:
    filepath = pathlib.Path(file_path)
    prompt = "Extract all visible text from this document as plain text.only nothings add extra things in this"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=filepath.read_bytes(),
                mime_type="application/pdf" if file_path.lower().endswith(".pdf") else "image/png",
            ),
            prompt,
        ],
    )

    extracted_text = response.text.strip() if response.text else ""
    num_pages = 1
    return extracted_text, num_pages
# ------------------------------------------------


# ------------ EMBEDDING SIMILARITY --------------
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def semantic_similarity(extracted: str, manual: str):
    emb1 = model.encode(normalize_text(extracted), convert_to_tensor=True)
    emb2 = model.encode(normalize_text(manual), convert_to_tensor=True)
    return util.cos_sim(emb1, emb2).item()
# ------------------------------------------------


# ---------------- STREAMLIT UI ------------------
st.set_page_config(page_title="OCR Embedding Comparison", layout="wide")
st.title("📊 OCR Evaluation (Semantic Similarity Only)")

uploaded_file = st.file_uploader("Upload a PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
manual_text = st.text_area("Paste your manually verified reference text here")

if uploaded_file and manual_text:
    # Save temp file
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    # Run OCRs
    with st.spinner("Running Tesseract OCR..."):
        tess_text, _ = extract_text_tesseract(temp_path)

    with st.spinner("Running Gemini OCR..."):
        gem_text, _ = extract_text_gemini(temp_path)

    # Show outputs
    st.subheader("🔹 Extracted Text")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🟦 Tesseract OCR")
        st.text_area("Extracted Text", tess_text, height=200)
    with col2:
        st.markdown("### 🟩 Gemini OCR")
        st.text_area("Extracted Text", gem_text, height=200)

    # --- Semantic Similarity ---
    st.subheader("📌 Embedding-based Similarity")

    for method, extracted in [("Tesseract", tess_text), ("Gemini", gem_text)]:
        sem_score = semantic_similarity(extracted, manual_text)
        st.write(f"**{method} OCR Semantic Similarity:** {sem_score:.2f}")

    os.remove(temp_path)
# ------------------------------------------------
