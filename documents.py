from docx import Document
import os

def extract_text_from_file(file_path: str) -> str:

    #Helper function to extract clean text from .txt and .docx attachments.

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Attachment not found at: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".docx":
        doc = Document(file_path)
        # Combine all paragraph text with newlines
        full_text = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(full_text)

    else:
        raise ValueError(f"Unsupported file extension: {ext}. Only .txt and .docx are supported.")
