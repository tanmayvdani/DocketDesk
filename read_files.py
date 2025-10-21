import sys
import os

def extract_text_from_docx(docx_path):
    try:
        from docx import Document
        document = Document(docx_path)
        full_text = []
        for para in document.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error extracting text from DOCX: {e}"

def extract_text_from_pdf(pdf_path):
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        full_text = []
        for page in reader.pages:
            full_text.append(page.extract_text())
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_files.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".docx":
        print(extract_text_from_docx(file_path))
    elif ext == ".pdf":
        print(extract_text_from_pdf(file_path))
    else:
        print(f"Unsupported file type: {ext}")
        sys.exit(1)
